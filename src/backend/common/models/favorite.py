from backend.common.models.mytba import MyTBAModel


class Favorite(MyTBAModel):
    """
    In order to make strongly consistent DB requests, instances of this class
    should be created with a parent that is the associated Account key.
    """

    def __init__(self, *args, **kwargs):
        super(Favorite, self).__init__(*args, **kwargs)
