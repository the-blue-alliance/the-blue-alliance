import unittest2

from consts.model_type import ModelType
from consts.notification_type import NotificationType

from tbans.utils.validation_utils import *


class TestValidationUtils(unittest2.TestCase):

    def test_validate_is_type_multiple(self):
        with self.assertRaises(Exception):
            validate_is_type(obj_type=str, ac="a", abc="abc")

    def test_validate_is_type_type(self):
        with self.assertRaises(TypeError):
            validate_is_type(obj_type=str, ac=1)

    def test_validate_is_type_none(self):
        with self.assertRaises(ValueError):
            validate_is_type(obj_type=str, ac="")

    def test_validate_is_type_valid(self):
        validate_is_type(obj_type=str, ac="abc")

    def test_validate_is_type_valid_none(self):
        validate_is_type(obj_type=str, not_empty=False, ac="")

    def test_validate_is_string_none(self):
        with self.assertRaises(TypeError):
            validate_is_string(efg=None)

    def test_validate_is_string_empty(self):
        with self.assertRaises(ValueError):
            validate_is_string(efg="")

    def test_validate_is_string_multiple(self):
        validate_is_string(abc="abc", ab="def")

    def test_validate_is_string(self):
        validate_is_string(efg="abc")

    def test_validate_model_params_model_type(self):
        with self.assertRaises(TypeError):
            validate_model_params("", "frc7332", [NotificationType.UPCOMING_MATCH, NotificationType.AWARDS])

    def test_validate_model_params_model_key_type(self):
        with self.assertRaises(TypeError):
            validate_model_params(ModelType.TEAM, 1, [NotificationType.UPCOMING_MATCH, NotificationType.AWARDS])

    def test_validate_model_params_model_key(self):
        with self.assertRaises(ValueError):
            validate_model_params(ModelType.TEAM, "", [NotificationType.UPCOMING_MATCH, NotificationType.AWARDS])

    def test_validate_model_params_notification_types_type(self):
        with self.assertRaises(TypeError):
            validate_model_params(ModelType.TEAM, "frc7332", 1)

    def test_validate_model_params_notification_types_list_type(self):
        with self.assertRaises(ValueError):
            validate_model_params(ModelType.TEAM, "frc7332", ["", NotificationType.UPCOMING_MATCH])

    def test_validate_model_params_notification_types_empty(self):
        validate_model_params(ModelType.TEAM, "frc7332", [])

    def test_validate_model_params(self):
        validate_model_params(ModelType.EVENT, "frc7332", [NotificationType.UPCOMING_MATCH, NotificationType.AWARDS])
