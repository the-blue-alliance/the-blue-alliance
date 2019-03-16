import logging


def validate_is_type(obj_type, not_empty=True, **kwargs):
    """
    Validates that a value is a not-None type.

    Examples:
        >>> validate_is_type(int, counter=1)
        # no throw
        >>> validate_is_type(basestring, some_key="")
        # will throw
        >>> validate_is_type(basestring, not_empty=False, some_key="")
        # no throw

    Args:
        obj_type (type): The type the kwarg value should be.
        not_empty (bool): If we should validate the kwarg value equates to None.
        kwargs: key/value pairs for the name/value of the strings to validate.

    Raises:
        Exception: If more than one kwarg is supplied.
        TypeError: If a param is not a string.
        ValueError: If a param is not a non-None string.
    """
    if len(kwargs) is not 1:
        raise Exception("validate_is_type may only have one kwarg")

    key, value = kwargs.items()[0]
    if not isinstance(value, obj_type):
        raise TypeError("{} must be a {} - got {}".format(key, obj_type.__name__, _type_name(value)))
    if not value and not_empty:
        raise ValueError("{} must not be empty".format(key))


def validate_is_string(**kwargs):
    """
    Validates that pararms are a non-empty strings.

    Examples:
        >>> validate_is_string(abc="abc")
        # no throw
        >>> validate_is_string(abc="")
        # will throw
        >>> validate_is_string(abc=1)
        # will throw

    Args:
        kwargs (string): key/value pairs for the name/value of the strings to validate.

    Raises:
        TypeError: If a param is not a string.
        ValueError: If a param is not a non-None string.
    """
    for key, value in kwargs.items():
        arg = {key: value}
        validate_is_type(basestring, **arg)


def validate_model_params(model_type, model_key, notification_types):
    """
    Method to DRY out validation for model_type, model_key, notification_types

    Args:
        model_type (int): ModelType constant from monorepo - Event, Team, Match, etc.
        model_key (string): Key for the model.
        notification_types (list, int): A list of NotificationType constants to get topics for.
    """
    # Ensure our model_type looks right.
    validate_is_type(int, not_empty=False, model_type=model_type)
    # Kick the model_key/notification_types validation out to a shared method.
    validate_model_key_and_notification_types(model_key, notification_types)


def validate_model_key_and_notification_types(model_key, notification_types):
    """
    Method to DRY out validation for keys/notification_types.

    Args:
        model_key (string): A key to validate.
        notification_types (list, int): A list of NotificationType constants to validate.
    """
    # Ensure our model_key looks right.
    validate_is_string(model_key=model_key)

    # Ensure our notification_types looks right.
    validate_is_type(list, not_empty=False, notification_types=notification_types)

    invalid_notification_types = [nt for nt in notification_types if not isinstance(nt, int)]
    if invalid_notification_types:
        raise ValueError('notification_types items must be ints')


def _type_name(typed_obj):
    """
    Get the name for a type for a given value.

    Args:
        typed_obj (any): The value to get the type for.

    Returns:
        string: Name of the type for the given value.
    """
    return type(typed_obj).__name__
