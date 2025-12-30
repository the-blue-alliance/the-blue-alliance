"""Stub for Google storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import calendar
import datetime
import hashlib

import six
import six.moves.http_client  # pyre-ignore[21]

from google.appengine.api import datastore
from google.appengine.api import namespace_manager
from google.appengine.api.blobstore import blobstore_stub
from google.appengine.ext import db

from backend.common.storage.clients.cloudstorage import common

__author__ = "yey@google.com (Ye Yuan)"

# pylint: disable=g-bad-name

# Default to the same type as production GCS.
_GCS_DEFAULT_CONTENT_TYPE = "application/octet-stream"


# TODO(b/72688911): This entity is heavily overloaded. Refactor.
# In production, this is at least three separate ones:
# 1. one for upload sessions.
# 2. one for uploaded files.
# 3. one for the metadata of uploaded files.
class _AE_GCSFileInfo_(db.Model):
    """Store GCS specific info.

    GCS allows user to define arbitrary metadata via header x-goog-meta-foo: bar.
    These headers are returned when user does a GET or HEAD on the object.

    Key name is blobkey.
    """

    # /bucket/filename.
    filename = db.StringProperty(required=True)
    finalized = db.BooleanProperty(required=True)
    # gcs options provided by user.
    # Do not set this directly. Use options.
    # e.g. {'x-goog-meta-foo': 'foo', 'x-goog-meta-bar': 'bar'}
    # -> ['x-goog-meta-foo:foo', 'x-goog-meta-bar:bar']
    raw_options = db.StringListProperty()
    # Finalizing a file should fill in the following fields.
    # total file size for finalized file.
    size = db.IntegerProperty()
    # start offset we expect for next uploaded contents.
    # -1 when file is finalized.
    next_offset = db.IntegerProperty(default=0)
    # UTC.
    creation = db.DateTimeProperty()
    # Do not set this directly. Use options.
    content_type = db.StringProperty(default=_GCS_DEFAULT_CONTENT_TYPE)
    etag = db.ByteStringProperty()

    def get_options(self):
        return dict(o.split(":", 1) for o in self.raw_options)

    def set_options(self, options_dict):
        self.raw_options = [
            "%s:%s" % (k.lower(), v) for k, v in six.iteritems(options_dict)
        ]
        if "content-type" in options_dict:
            self.content_type = options_dict["content-type"]

    # Can't use options.setter for 25 compatibility
    options = property(get_options, set_options)

    @classmethod
    def kind(cls):
        # pylint: disable=protected-access
        return blobstore_stub._GS_INFO_KIND


class _AE_GCSPartialFile_(db.Model):
    """Store partial content for uploading files."""

    # key name of this entity is the start offset of this content
    # with respect to the file, inclusive.
    # A "start" field isn't used to avoid a separate index
    # when doing queries over it.

    # end offset of this content. Exclusive.
    end = db.IntegerProperty(required=True)
    # A storage key for the partial content.
    partial_content = db.TextProperty(required=True)


class CloudStorageStub(object):
    """Google Cloud Storage stub implementation.

    We use blobstore stub to store files. All metadata are stored
    in _AE_GCSFileInfo_.

    Note: this Google Cloud Storage stub is designed to work with
    appengine.ext.cloudstorage.storage_api.py.
    It only implements the part of GCS storage_api.py uses, and its interface
    maps to GCS XML APIs.
    """

    def __init__(self, blob_storage):
        """Initialize.

        Args:
          blob_storage:
              appengine.api.blobstore.blobstore_stub.BlobStorage instance
        """
        self.blob_storage = blob_storage

    def _filename_to_blobkey(self, filename):
        """Get blobkey for filename.

        Args:
          filename: gcs filename of form /bucket/filename.

        Returns:
          blobinfo's datastore's key name, aka, blobkey.
        """
        common.validate_file_path(filename)

        return blobstore_stub.BlobstoreServiceStub.CreateEncodedGoogleStorageKey(
            filename[1:]
        )

    @db.non_transactional
    def post_start_creation(self, filename, options):
        """Start object creation with a POST.

        This implements the resumable upload XML API.

        Only major limitation of current implementation is that we don't
        support multiple upload sessions for the same GCS file. Previous
        _AE_GCSFileInfo (which represents either a finalized file, or
        an upload session) will be removed when a new upload session is
        created.

        Args:
          filename: gcs filename of form /bucket/filename.
          options: a dict containing all user specified request headers.
            e.g. {'content-type': 'foo', 'x-goog-meta-bar': 'bar'}.

        Returns:
          a token (blobkey) used for continuing upload.
        """
        ns = namespace_manager.get_namespace()
        try:
            namespace_manager.set_namespace("")
            common.validate_file_path(filename)
            token = self._filename_to_blobkey(filename)
            key = datastore.Key.from_path(
                _AE_GCSFileInfo_.kind(), token, _app="testbed-test"
            )
            gcs_file = _AE_GCSFileInfo_.get(key)

            self._cleanup_old_file(gcs_file)
            new_file = _AE_GCSFileInfo_(
                key_name=token, filename=filename, finalized=False, _app="testbed-test"
            )
            new_file.options = options
            new_file.put()
            return token
        finally:
            namespace_manager.set_namespace(ns)

    # Note: this should run in a xg transaction but only HRD supports it.
    @db.non_transactional
    def _cleanup_old_file(self, gcs_file):
        """Clean up the old version of a file.

        The old version may or may not be finalized yet. Either way,
        when user tries to create a file that already exists, we delete the
        old version first.

        Args:
          gcs_file: an instance of _AE_GCSFileInfo_.
        """
        if gcs_file:
            if gcs_file.finalized:
                blobkey = gcs_file.key().name()
                self.blob_storage.DeleteBlob(blobkey)
            else:
                db.delete(
                    _AE_GCSPartialFile_.all(_app="testbed-test").ancestor(gcs_file)
                )
            gcs_file.delete()

    @db.non_transactional
    def put_empty(self, token):
        """Empty put is used to query upload progress.

        The file must has not finished upload.

        Args:
          token: upload token returned by post_start_creation.

        Returns:
          last offset uploaded. -1 if none has been uploaded.

        Raises:
          ValueError: if token matches no in progress uploads.
        """
        ns = namespace_manager.get_namespace()
        try:
            namespace_manager.set_namespace("")
            key = datastore.Key.from_path(
                _AE_GCSFileInfo_.kind(), token, _app="testbed-test"
            )
            gcs_file = _AE_GCSFileInfo_.get(key)
            if not gcs_file:
                raise ValueError("Invalid token", six.moves.http_client.BAD_REQUEST)
            return gcs_file.next_offset - 1
        finally:
            namespace_manager.set_namespace(ns)

    @db.non_transactional
    def put_continue_creation(
        self, token, content, content_range, length=None, _upload_filename=None
    ):
        """Continue object upload with PUTs.

        This implements the resumable upload XML API.

        Args:
          token: upload token returned by post_start_creation.
          content: object content. None if no content was provided with this
            PUT request.
          content_range: a (start, end) tuple specifying the content range of this
            chunk. Both are inclusive according to XML API. None is content is None.
          length: file length, if this is the last chunk of file content.
          _upload_filename: internal use. Might be removed any time! This is
            used by blobstore to pass in the upload filename from user.

        Returns:
          _AE_GCSFileInfo entity for this file if the file is finalized.

        Raises:
          ValueError: if something is invalid. The exception.args is a tuple of
          (msg, http status code).
        """
        # TODO(b/72688846): Replace all HTTP status code with prod ones once scotty
        # finalizes them on prod.
        ns = namespace_manager.get_namespace()
        try:
            namespace_manager.set_namespace("")
            key = datastore.Key.from_path(
                _AE_GCSFileInfo_.kind(), token, _app="testbed-test"
            )
            gcs_file = _AE_GCSFileInfo_.get(key)
            if not gcs_file:
                raise ValueError("Invalid token", six.moves.http_client.BAD_REQUEST)
            if gcs_file.next_offset == -1:
                raise ValueError(
                    "Received more uploads after file %s "
                    "was finalized." % gcs_file.filename,
                    six.moves.http_client.OK,
                )
            if content:
                start, end = content_range
                if len(content) != (end - start + 1):
                    raise ValueError(
                        "Invalid content range %d-%d" % content_range,
                        six.moves.http_client.REQUESTED_RANGE_NOT_SATISFIABLE,
                    )
                # No hole in upload.
                if start > gcs_file.next_offset:
                    raise ValueError(
                        "Expect start offset %s, got %s"
                        % (gcs_file.next_offset, start),
                        six.moves.http_client.REQUESTED_RANGE_NOT_SATISFIABLE,
                    )
                # No overwrites of uploads.
                elif end < gcs_file.next_offset:
                    return
                else:
                    # Truncate content to only those we haven't saved.
                    content = content[gcs_file.next_offset - start :]
                    start = gcs_file.next_offset
                    blobkey = "%s-%d-%d" % (token, start, end)
                    self.blob_storage.StoreBlob(blobkey, six.BytesIO(content))
                    new_content = _AE_GCSPartialFile_(
                        parent=gcs_file,
                        _app="testbed-test",
                        # left-aligned zero padding 20 width.
                        key_name="%020d" % start,
                        partial_content=blobkey,
                        start=start,
                        end=end + 1,
                    )
                    new_content.put()
                    gcs_file.next_offset = end + 1
                    gcs_file.put()
            if length is not None and length != gcs_file.next_offset:
                raise ValueError(
                    "Got finalization request with wrong file length. "
                    "Expecting %s, got %s" % (gcs_file.next_offset, length),
                    six.moves.http_client.REQUESTED_RANGE_NOT_SATISFIABLE,
                )
            elif length is not None:
                return self._end_creation(token, _upload_filename)
        finally:
            namespace_manager.set_namespace(ns)

    @db.non_transactional
    def put_copy(self, src, dst, options):
        """Copy file from src to dst.

        Metadata is copied.

        Args:
          src: /bucket/filename. This file must exist.
          dst: /bucket/filename.
          options: a dict containing all user specified request headers.
            e.g. {'content-type': 'foo', 'x-goog-meta-bar': 'bar'}. If None,
            old metadata is copied.
        """
        common.validate_file_path(src)
        common.validate_file_path(dst)

        # Fetch source metadata and copy.
        ns = namespace_manager.get_namespace()
        try:
            namespace_manager.set_namespace("")
            src_blobkey = self._filename_to_blobkey(src)
            key = datastore.Key.from_path(
                _AE_GCSFileInfo_.kind(), src_blobkey, _app="testbed-test"
            )
            source = _AE_GCSFileInfo_.get(key)
            token = self._filename_to_blobkey(dst)
            new_file = _AE_GCSFileInfo_(
                key_name=token, filename=dst, finalized=True, _app="testbed-test"
            )
            if options:
                new_file.options = options
            else:
                new_file.options = source.options
            new_file.etag = source.etag
            new_file.size = source.size
            new_file.creation = source.creation
            new_file.put()
        finally:
            namespace_manager.set_namespace(ns)

        # In case of copying to oneself.
        if src_blobkey != token:
            # Fetch source content and copy.
            local_file = self.blob_storage.OpenBlob(src_blobkey)
            self.blob_storage.StoreBlob(token, local_file)

    @db.non_transactional
    def _end_creation(self, token, _upload_filename):
        """End object upload.

        Args:
          token: upload token returned by post_start_creation.

        Returns:
          _AE_GCSFileInfo Entity for this file.

        Raises:
          ValueError: if token is invalid. Or file is corrupted during upload.

        Save file content to blobstore. Save blobinfo and _AE_GCSFileInfo.
        """
        key = datastore.Key.from_path(
            _AE_GCSFileInfo_.kind(), token, _app="testbed-test"
        )
        gcs_file = _AE_GCSFileInfo_.get(key)
        if not gcs_file:
            raise ValueError("Invalid token")
        if gcs_file.finalized:
            return gcs_file

        error_msg, content = self._get_content(gcs_file)
        if error_msg:
            raise ValueError(error_msg)

        gcs_file.etag = hashlib.md5(six.ensure_binary(content)).hexdigest()
        gcs_file.creation = datetime.datetime.now(datetime.UTC)
        gcs_file.size = len(content)

        # Create blob info for now to be consistent with prod.
        # TODO(b/72688578): Remove when we stop creating blob info for gcs files.
        blob_info = datastore.Entity(
            "__BlobInfo__", name=str(token), namespace="", _app="testbed-test"
        )
        blob_info["content_type"] = gcs_file.content_type
        blob_info["creation"] = gcs_file.creation
        blob_info["filename"] = _upload_filename
        blob_info["md5_hash"] = gcs_file.etag
        blob_info["size"] = gcs_file.size
        datastore.Put(blob_info)

        self.blob_storage.StoreBlob(token, six.BytesIO(content))

        gcs_file.finalized = True
        # Accepting no more uploads.
        gcs_file.next_offset = -1
        gcs_file.put()
        return gcs_file

    @db.transactional(propagation=db.INDEPENDENT, app="testbed-test")
    def _get_content(self, gcs_file):
        """Aggregate all partial content of the gcs_file.

        Args:
          gcs_file: an instance of _AE_GCSFileInfo_.

        Returns:
          (error_msg, content) tuple. error_msg is set if the file is
          corrupted during upload. Otherwise content is set to the
          aggregation of all partial contents.
        """
        content = b""
        previous_end = 0
        error_msg = ""
        for partial in (
            _AE_GCSPartialFile_.all(namespace="", _app="testbed-test")
            .ancestor(gcs_file)
            .order("__key__")
        ):
            start = int(partial.key().name())
            if not error_msg:
                if start < previous_end:
                    error_msg = "File is corrupted due to missing chunks."
                elif start > previous_end:
                    error_msg = "File is corrupted due to overlapping chunks"
                previous_end = partial.end
                content += self.blob_storage.OpenBlob(partial.partial_content).read()
                self.blob_storage.DeleteBlob(partial.partial_content)
            partial.delete()
        if error_msg:
            gcs_file.delete()
            content = b""
        return error_msg, content

    @db.non_transactional
    def get_bucket(self, bucketpath, prefix, marker, max_keys, delimiter):
        """Get bucket listing with a GET.

        How GCS listbucket work in production:
        GCS tries to return as many items as possible in a single response. If
        there are more items satisfying user's query and the current request
        took too long (e.g spent on skipping files in a subdir) or items to return
        gets too big (> max_keys), it returns fast and sets IsTruncated
        and NextMarker for continuation. They serve redundant purpose: if
        NextMarker is set, IsTruncated is True.

        Note NextMarker is not where GCS scan left off. It is
        only valid for the exact same type of query the marker was generated from.
        For example, if a marker is generated from query with delimiter, the marker
        is the name of a subdir (instead of the last file within the subdir). Thus
        you can't use this marker to issue a query without delimiter.

        Args:
          bucketpath: gcs bucket path of form '/bucket'
          prefix: prefix to limit listing.
          marker: a str after which to start listing. Exclusive.
          max_keys: max items we scan & return.
          delimiter: delimiter for directory.

        See https://developers.google.com/storage/docs/reference-methods#getbucket
        for details.

        Returns:
          A tuple of (a list of GCSFileStat for files or directories sorted by
          filename, next_marker to use as next marker, is_truncated boolean to
          indicate if there are more results satisfying query).
        """
        common.validate_bucket_path(bucketpath)
        q = _AE_GCSFileInfo_.all(namespace="", _app="testbed-test")
        fully_qualified_prefix = "/".join([bucketpath, prefix])
        if marker:
            q.filter("filename >", "/".join([bucketpath, marker]))
        else:
            q.filter("filename >=", fully_qualified_prefix)

        result = set()
        name = None
        first = True
        first_dir = None
        for info in q.run():
            # Stop if filename isn't under prefix.
            if not info.filename.startswith(fully_qualified_prefix):
                break
            if len(result) == max_keys:
                break

            # Deal with eventual consistent queries.
            info = db.get(info.key())
            if not info:
                continue

            name = info.filename
            if delimiter:
                # Index of delimiter after prefix.
                start_index = name.find(delimiter, len(fully_qualified_prefix))
                if start_index != -1:
                    name = name[: start_index + len(delimiter)]
                    # If marker is present, we need to skip the first sub dir
                    # because it is already returned by last request.
                    if marker and (first or name == first_dir):
                        first = False
                        first_dir = name
                    # Otherwise just add a sub dir.
                    else:
                        result.add(
                            common.GCSFileStat(
                                name,
                                st_size=None,
                                st_ctime=None,
                                etag=None,
                                is_dir=True,
                            )
                        )
                    continue

            # Only return finalized files
            if info.finalized:
                first = False
                result.add(
                    common.GCSFileStat(
                        filename=name,
                        st_size=info.size,
                        st_ctime=calendar.timegm(info.creation.utctimetuple()),
                        etag=info.etag,
                    )
                )

        def is_truncated():
            """Check if there are more results satisfying the query."""
            if not result:
                return False
            q = _AE_GCSFileInfo_.all(namespace="", _app="testbed-test")
            q.filter("filename >", name)
            info = None
            # If name is a subdir.
            if delimiter and name.endswith(delimiter):
                # Needs to find the file after current sub dir.
                for info in q.run():
                    if not info.filename.startswith(name):
                        break
                if info is not None and info.filename.startswith(name):
                    info = None
            else:
                info = q.get()
            if info is None or not info.filename.startswith(fully_qualified_prefix):
                return False
            return True

        result = list(result)
        result.sort()
        truncated = is_truncated()
        next_marker = name if truncated else None

        return result, next_marker, truncated

    @db.non_transactional
    def get_object(self, filename, start=0, end=None):
        """Get file content with a GET.

        Args:
          filename: gcs filename of form '/bucket/filename'.
          start: start offset to request. Inclusive.
          end: end offset to request. Inclusive.

        Returns:
          The segment of file content requested.

        Raises:
          ValueError: if file doesn't exist.
        """
        common.validate_file_path(filename)
        blobkey = self._filename_to_blobkey(filename)
        key = datastore.Key.from_path(
            _AE_GCSFileInfo_.kind(), blobkey, _app="testbed-test"
        )
        gcsfileinfo = db.get(key)
        if not gcsfileinfo or not gcsfileinfo.finalized:
            raise ValueError("File does not exist.")
        local_file = self.blob_storage.OpenBlob(blobkey)
        local_file.seek(start)
        if end:
            return local_file.read(end - start + 1)
        else:
            return local_file.read()

    @db.non_transactional
    def head_object(self, filename):
        """Get file stat with a HEAD.

        Args:
          filename: gcs filename of form '/bucket/filename'

        Returns:
          A GCSFileStat object containing file stat. None if file doesn't exist.
        """
        common.validate_file_path(filename)
        blobkey = self._filename_to_blobkey(filename)
        key = datastore.Key.from_path(
            _AE_GCSFileInfo_.kind(), blobkey, _app="testbed-test"
        )
        info = db.get(key)
        if info and info.finalized:
            metadata = common.get_metadata(info.options)
            filestat = common.GCSFileStat(
                filename=info.filename,
                st_size=info.size,
                etag=info.etag,
                st_ctime=calendar.timegm(info.creation.utctimetuple()),
                content_type=info.content_type,
                metadata=metadata,
            )
            return filestat
        return None

    @db.non_transactional
    def delete_object(self, filename):
        """Delete file with a DELETE.

        Args:
          filename: gcs filename of form '/bucket/filename'

        Returns:
          True if file is deleted. False if file doesn't exist.
        """
        common.validate_file_path(filename)
        blobkey = self._filename_to_blobkey(filename)
        key = datastore.Key.from_path(
            _AE_GCSFileInfo_.kind(), blobkey, _app="testbed-test"
        )
        gcsfileinfo = db.get(key)
        if not gcsfileinfo:
            return False

        blobstore_stub.BlobstoreServiceStub.DeleteBlob(blobkey, self.blob_storage)
        return True
