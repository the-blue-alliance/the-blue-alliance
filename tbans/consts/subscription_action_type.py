class SubscriptionActionType:
    """
    Constants for subscription actions
    """

    ADD = 0  # Subscribe
    REMOVE = 1  # Unsubscribe

    batch_actions = [ADD, REMOVE]  # Supported batch actions

    BATCH_METHODS = {
        ADD: 'v1:batchAdd',
        REMOVE: 'v1:batchRemove'
    }
