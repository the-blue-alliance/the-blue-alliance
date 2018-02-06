import json
import unittest2

from datafeeds.parsers.fms_api.fms_api_team_avatar_parser import FMSAPITeamAvatarParser

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.district import District
from consts.media_type import MediaType


class TestFMSAPITeamAvatarParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_parse_team_with_avatar(self):
        with open('test_data/fms_api/2018_avatars_frc1741.json', 'r') as f:
            models, more_pages = FMSAPITeamAvatarParser(2018).parse(json.loads(f.read()))

            self.assertFalse(more_pages)
            self.assertEqual(len(models), 1)

            # Ensure we get the proper Media model back
            media = models[0]
            self.assertEqual(media.key, ndb.Key('Media', 'avatar_avatar_2018_frc1741'))
            self.assertEqual(media.foreign_key, 'avatar_2018_frc1741')
            self.assertEqual(media.media_type_enum, MediaType.AVATAR)
            self.assertEqual(media.references, [ndb.Key('Team', 'frc1741')])
            self.assertEqual(media.year, 2018)
            self.assertEqual(media.details_json, '{"base64Image": "iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAABGdBTUEAALGOfPtRkwAAACBjSFJNAACHDwAAjA8AAP1SAACBQAAAfXkAAOmLAAA85QAAGcxzPIV3AAAKOWlDQ1BQaG90b3Nob3AgSUNDIHByb2ZpbGUAAEjHnZZ3VFTXFofPvXd6oc0wAlKG3rvAANJ7k15FYZgZYCgDDjM0sSGiAhFFRJoiSFDEgNFQJFZEsRAUVLAHJAgoMRhFVCxvRtaLrqy89/Ly++Osb+2z97n77L3PWhcAkqcvl5cGSwGQyhPwgzyc6RGRUXTsAIABHmCAKQBMVka6X7B7CBDJy82FniFyAl8EAfB6WLwCcNPQM4BOB/+fpFnpfIHomAARm7M5GSwRF4g4JUuQLrbPipgalyxmGCVmvihBEcuJOWGRDT77LLKjmNmpPLaIxTmns1PZYu4V8bZMIUfEiK+ICzO5nCwR3xKxRoowlSviN+LYVA4zAwAUSWwXcFiJIjYRMYkfEuQi4uUA4EgJX3HcVyzgZAvEl3JJS8/hcxMSBXQdli7d1NqaQffkZKVwBALDACYrmcln013SUtOZvBwAFu/8WTLi2tJFRbY0tba0NDQzMv2qUP91829K3NtFehn4uWcQrf+L7a/80hoAYMyJarPziy2uCoDOLQDI3fti0zgAgKSobx3Xv7oPTTwviQJBuo2xcVZWlhGXwzISF/QP/U+Hv6GvvmckPu6P8tBdOfFMYYqALq4bKy0lTcinZ6QzWRy64Z+H+B8H/nUeBkGceA6fwxNFhImmjMtLELWbx+YKuGk8Opf3n5r4D8P+pMW5FonS+BFQY4yA1HUqQH7tBygKESDR+8Vd/6NvvvgwIH554SqTi3P/7zf9Z8Gl4iWDm/A5ziUohM4S8jMX98TPEqABAUgCKpAHykAd6ABDYAasgC1wBG7AG/iDEBAJVgMWSASpgA+yQB7YBApBMdgJ9oBqUAcaQTNoBcdBJzgFzoNL4Bq4AW6D+2AUTIBnYBa8BgsQBGEhMkSB5CEVSBPSh8wgBmQPuUG+UBAUCcVCCRAPEkJ50GaoGCqDqqF6qBn6HjoJnYeuQIPQXWgMmoZ+h97BCEyCqbASrAUbwwzYCfaBQ+BVcAK8Bs6FC+AdcCXcAB+FO+Dz8DX4NjwKP4PnEIAQERqiihgiDMQF8UeikHiEj6xHipAKpAFpRbqRPuQmMorMIG9RGBQFRUcZomxRnqhQFAu1BrUeVYKqRh1GdaB6UTdRY6hZ1Ec0Ga2I1kfboL3QEegEdBa6EF2BbkK3oy+ib6Mn0K8xGAwNo42xwnhiIjFJmLWYEsw+TBvmHGYQM46Zw2Kx8lh9rB3WH8vECrCF2CrsUexZ7BB2AvsGR8Sp4Mxw7rgoHA+Xj6vAHcGdwQ3hJnELeCm8Jt4G749n43PwpfhGfDf+On4Cv0CQJmgT7AghhCTCJkIloZVwkfCA8JJIJKoRrYmBRC5xI7GSeIx4mThGfEuSIemRXEjRJCFpB+kQ6RzpLuklmUzWIjuSo8gC8g5yM/kC+RH5jQRFwkjCS4ItsUGiRqJDYkjiuSReUlPSSXK1ZK5kheQJyeuSM1J4KS0pFymm1HqpGqmTUiNSc9IUaVNpf+lU6RLpI9JXpKdksDJaMm4ybJkCmYMyF2TGKQhFneJCYVE2UxopFykTVAxVm+pFTaIWU7+jDlBnZWVkl8mGyWbL1sielh2lITQtmhcthVZKO04bpr1borTEaQlnyfYlrUuGlszLLZVzlOPIFcm1yd2WeydPl3eTT5bfJd8p/1ABpaCnEKiQpbBf4aLCzFLqUtulrKVFS48vvacIK+opBimuVTyo2K84p6Ss5KGUrlSldEFpRpmm7KicpFyufEZ5WoWiYq/CVSlXOavylC5Ld6Kn0CvpvfRZVUVVT1Whar3qgOqCmrZaqFq+WpvaQ3WCOkM9Xr1cvUd9VkNFw08jT6NF454mXpOhmai5V7NPc15LWytca6tWp9aUtpy2l3audov2Ax2yjoPOGp0GnVu6GF2GbrLuPt0berCehV6iXo3edX1Y31Kfq79Pf9AAbWBtwDNoMBgxJBk6GWYathiOGdGMfI3yjTqNnhtrGEcZ7zLuM/5oYmGSYtJoct9UxtTbNN+02/R3Mz0zllmN2S1zsrm7+QbzLvMXy/SXcZbtX3bHgmLhZ7HVosfig6WVJd+y1XLaSsMq1qrWaoRBZQQwShiXrdHWztYbrE9Zv7WxtBHYHLf5zdbQNtn2iO3Ucu3lnOWNy8ft1OyYdvV2o/Z0+1j7A/ajDqoOTIcGh8eO6o5sxybHSSddpySno07PnU2c+c7tzvMuNi7rXM65Iq4erkWuA24ybqFu1W6P3NXcE9xb3Gc9LDzWepzzRHv6eO7yHPFS8mJ5NXvNelt5r/Pu9SH5BPtU+zz21fPl+3b7wX7efrv9HqzQXMFb0ekP/L38d/s/DNAOWBPwYyAmMCCwJvBJkGlQXlBfMCU4JvhI8OsQ55DSkPuhOqHC0J4wybDosOaw+XDX8LLw0QjjiHUR1yIVIrmRXVHYqLCopqi5lW4r96yciLaILoweXqW9KnvVldUKq1NWn46RjGHGnIhFx4bHHol9z/RnNjDn4rziauNmWS6svaxnbEd2OXuaY8cp40zG28WXxU8l2CXsTphOdEisSJzhunCruS+SPJPqkuaT/ZMPJX9KCU9pS8Wlxqae5Mnwknm9acpp2WmD6frphemja2zW7Fkzy/fhN2VAGasyugRU0c9Uv1BHuEU4lmmfWZP5Jiss60S2dDYvuz9HL2d7zmSue+63a1FrWWt78lTzNuWNrXNaV78eWh+3vmeD+oaCDRMbPTYe3kTYlLzpp3yT/LL8V5vDN3cXKBVsLBjf4rGlpVCikF84stV2a9021DbutoHt5turtn8sYhddLTYprih+X8IqufqN6TeV33zaEb9joNSydP9OzE7ezuFdDrsOl0mX5ZaN7/bb3VFOLy8qf7UnZs+VimUVdXsJe4V7Ryt9K7uqNKp2Vr2vTqy+XeNc01arWLu9dn4fe9/Qfsf9rXVKdcV17w5wD9yp96jvaNBqqDiIOZh58EljWGPft4xvm5sUmoqbPhziHRo9HHS4t9mqufmI4pHSFrhF2DJ9NProje9cv+tqNWytb6O1FR8Dx4THnn4f+/3wcZ/jPScYJ1p/0Pyhtp3SXtQBdeR0zHYmdo52RXYNnvQ+2dNt293+o9GPh06pnqo5LXu69AzhTMGZT2dzz86dSz83cz7h/HhPTM/9CxEXbvUG9g5c9Ll4+ZL7pQt9Tn1nL9tdPnXF5srJq4yrndcsr3X0W/S3/2TxU/uA5UDHdavrXTesb3QPLh88M+QwdP6m681Lt7xuXbu94vbgcOjwnZHokdE77DtTd1PuvriXeW/h/sYH6AdFD6UeVjxSfNTws+7PbaOWo6fHXMf6Hwc/vj/OGn/2S8Yv7ycKnpCfVEyqTDZPmU2dmnafvvF05dOJZ+nPFmYKf5X+tfa5zvMffnP8rX82YnbiBf/Fp99LXsq/PPRq2aueuYC5R69TXy/MF72Rf3P4LeNt37vwd5MLWe+x7ys/6H7o/ujz8cGn1E+f/gUDmPP8usTo0wAAAAlwSFlzAAALEgAACxIB0t1+/AAADWZJREFUWEe1WAlUU2cW/sVWx9Y6x7XWpe5WETdEPa3OOdM57ekynZm2c6bnzKk6U21dWpXiguybS11QFllFNtlJAiEJgYSwJBASEkLCIooKoqJF2cTaqrX1zr1/CItNPc7YuSffef/L+9/7v3e3/97H0rLFLF2Qh0cCjcX8aIP12tCxUFLIwiJimKvbLnboyDGWlSObmZqV25khyOssLa/q1FRWd1XVNCyNiIpln2/dxqJi4pipromVlhuYRlvNSjV6liWS8mcFHfyGeXj5MF//QLZz1x5WVKph8jwpmzV5Cls8bz7ji9oIWsdDCdqI90GJ568jIZaYksX2eXqt9g/cX5cpkjanZOYCXocyrRHKdSYw1Jy9cjQ4pH6n2+6PxdJCpjPWEsFpaq0xr0StY3gPyxDJ2IFvjnCCPn4BbOfuPoISK0GnufMYJzBAcqgG6b8MoYSOMjwvIAKIZoQcf/LTyRmXEs6kQ76iFHAeKFQaEIjloCrVgrbKDCJxPsgKVO16U4O8RKOXI0GLWlsNxWqdKkMklcclpTG/gCBOjo5furqxvAIlK5TmWzVoJThgOjQTql7GTZidK2ciqWKGUKJU40tw7dDxTGYO4DxITBVAjlQJuDjXmFxZBkIkJy0ohmKNHko1VaAz1vHraHYoI1QYOIpKKyFfqYbwyJhK1KBjwP6DjODu6c3qzzWxfLGEzX7FDsGs3HwWGRvPvjkSzE6ERTK3XXte2un6NSeXgqQSUrNBUqDiWsqVKqCgSA15+UVIsJovLEFy6H8cpXiO5gQlalNRUsGvq8p0fO7Njh641dkDCx0dYcacOXO2b9/B1n+2kYWEhDIAYJmpaQM+SMRsfiaSKjmxbV9tpwCYvnnr1pO79rhDhkAC0sISriWj+SwnR5okcnlyFahJM+UGqNDX8DHXGJIjLemNtVBbf57Mysmqyirh8tUb0HrtBnzwwV9ggdPixD++867j2j+9xYKPHecEM1JS2ayXX0EN9hO0+ZuUpWSIWEh4FDt87MRriSmZUFxuBAwKqESfUhSXg1im5MRy0byV1fVwsa0TapqugPl8K5j50QpDQzO0tN/G9QDarn+LL1jKiVvqzoFYXowvq4Zb3z0EtUYL4SEhf/1i82bm4+PLCcptPmjToM3EiDXo7C+TJrPEBQfRF7nZUlBb0sJi9DkFxCWlI7EGqEUywaER8Nm/N0KAty/4enqDn6ePFV4+4OXuBb7u+8Cgr4Kb9x5BlbkRzl9ogR8ePAST5Sy6hwaJt/MXQIkMCgj852cbN23AsUtyfAKbPn7i4wTznPDYjRCi+bbg/yDMK4Bs1B4GDiSkZIO+ug5KdGaISkiBHTtcwXnFCmCM/SocEB++9z74BR2C5LRMzqT58jW4easTqs0N0Hr1OnR234Z79+5DTHQsJCUkQo3BcGXq2PHLJ4wcxeZOmTpgYoQqHVPFmQwRhww1Rz5VoTdxkD/lYxqJjk2AefPm2yX0JLw6bRoUKVRw8Wo79Ny5Cz2938Gtjm5ov9mJQdPNyZMkxSfBGpeVjR+++x57c83a/iBxxgiuTssSQ3K6EGQYEJTHKPIwf4FKrYcSHPsHBsGyhY52CTwNli9YCEajCe4+fAQdXbdRk13QffsOXENT32i/BXUNTVCmt0BD681LsfHJLv5BB6wE0e9kcYlp93F34KlDi5ojh6Y0oa40gShfBe77PMHFabHdhf8brFy8BATCPLj3E0Dvd9+jBjugtsEa5ZSaFOibYaEnH+719C7x9PZlTJBXyGLjz/xuzz6PgmTcFapqzoIGieF+yVOFFpOtEE3vvMjJ7oL/C+hFqw0mePDTzzw7NJ5vhsamZqgwNUJIcAjMnTrNtHnTF6NCcL/nW1ladi5LOJMpSsRELMNtizRIpjVYzkOepIC/tb2FngXOjovAoNPD+ZY2nhvLMbmTSxUWlUFWVk65Tm9mZRVGxquI46ERLDMnXywtKMFJ1iSr0Rp4OonEoLC3wLNi5qTJSEQE5nOXoQgJYgHBrVahN4Ol6UrlunXr2bhx4xhzwwpip5tbSnhUXG8J7p+VBgtqrwqwPILImHiYNn263QWeFbMnTwGsYkBeXMH3bNIe+b35bDOER8R8j3OECPRBkYRlCnJvSHB3oDegwOAZv7EFDh4+1v9Amzx+bk8Gz6Hji2wYTB495hf30vj4sRNgwV2I1iXfrz3XAjGnEmGZi8vdv//jE8awbjuK6NJWWXjFQeQI1Q0XISo6zu5DB58/Lvbm28TeNT8PL1BpTVCIOZbKtFxUFB3TMgS9AklhMBaR1jLIRsw2NtRfgITTSXYfOhijhw3vu/JLAmOYw5Dzx6/T+IB/EBjqLkIu7vFCcQHIMUh1uGMVY/GBRS0QwQ4sJDkxG6gs0prOwum4gQCxie381/5/kti7x2uvB2iM9bhBiPi2StWPCGsA2jAwR3dhKJPG+kqkCiOquhwDxQwt129BZESs3Yc+zX/2xN59rtt3Qh5uo1QhUalG5k1KE0IuVjzSovIuhok5ymg510NFZhFe1Bst0NLaBh13foCUpFS7D7V3/iTY5CU7Jt+y6QsowpKOFET5kFId1QJhqJyt274CaxRn594oVKlBWaLFbacJjKY6qL94DUoUil8sMvjcNn4SsCrhc0mmjhvP/7MJjfcHHgDsKrhJCUKJAtPbaXBeufIeXhcw11272bYdO1MyBeJeM0YubT2k6gut30JhoXLIYr8VsJziR9rfC1FrVLySD1LPk4eFrY//frrei2DMB3eSSOxbK6os4lYsxe/+cA96sRy6fKUNjJisc7Azo4f9P3ASzShCX6MmjMilYjVF2gwOjXyA14sQjJVpDQxtzzByRFSO9975Hjq7enid9vBnAF1VNYwdO9buAs+C9evWYxErAOxmeVNGoNaVyIaGR+tWODvjNJSa+gssV1Iwcq+Hl/x0Yio2Mzd5MUm1Wld3D9y5/xNUaHW/SallAz2LWoesvMJ+cqTBHAwQPx9/cJw1W+exdx8LOnSYMawimEZfIzeZLD9evNQC19s7sMLFQrKnl5fkVLhaGptBmCOFN5yfXOI/DVYtWQqR0adBKC1CjUn7zCsGbDUAm3mIR+IHDx5+eODwUfXR4yGMhUVEs2MnwlZearlST5HVQeZF7ZEftt24CXIsYJWYuA11FyDowCFY/NoCuws/DZZhRU0FCGmKyKX1kbMR5M1ZUQXEJWe0jp8w4fWJkyYxNnvuXPb7CROYphxDF+XOj4/owLVHZRf1JVevfcv7Eik6cEpaNrz5+hswyg6BJ4HMGhIWxYMiHftsW2AQORoLsEETF5TyHLh+w7/a8J6h8ur06X9ovdrWrRBLFMcCAv2IZI5Eyb8S1J9tstaHhlpoaGmHNCTp7+0HX2Nnt3zpMruECEuxCv984ybY7boLjhw5DmKlBtJQU4M1R+TyseSKiUuC+OR0iEtMfTDyhVHv4v1WcXAYxoYPH87HLi4uyxxfmz+GxkGBQTFEknoF6mEp05M2qfKtQZ+83HEPyrFxDw2LAG93DyTsC7tc3fqx88vt4OsXCMmoJbnGCELsa1LRhFZitm89YiiqqAZ3D+/yV2fO3LBi5crNy5cvx1auT4YN6xugjBgxsm80IHv37EnV6GpQiyZsA8wg7vuiQM08jfMVZaDHhtzSdBVKsBvLVaj7IcaXEheWQXZuPhKzaYyIWfMd+Vyhugr27POWDHNwQGcbkOeeew65DSJHQlp0cLBqsl8cHJiuun6v1mD5Wa4s5VUG9S3xZzL5t5lTielIQM6LzeR0wSC/smooHY9EhDBYaxStVEp9um5DYN9KqKARfaNfEZuZly93ZpgGWOypBJZ8JuMFNOlXmMgfJaZk81KMClsilURJFrVD1Q9p1Lb443icXCoiWywHEVpikZPTp7jki3zhp5F58+ez6rom1tR6k5kwgRvMjXOwDWglYvRlQYb7JH2hom80GTly/mGJzonsAKlBmsJUIsJ8l4emFuO9QiRFmqP99gxe9/bxgzVr134yBzPJ4qVL2ZKly9gip8U8s8yZN4/NRQyRjz76mDVducWK1ZVUyOJRxzCKGUZvlaxAxf1v0+YtcOhI8PnTyRnXAvYf4uQe1xIhB4MCO0U4ejwMfAP2cxwJDuNphO7bgs/x8QtowfSySqnWM5lSzSFRlLEcmdKKfOt23C9vvfU2Mzc2c3IE6ktxJ2HhmMzdPb1K1ZXVdY4LHetx6kTEirnz5zeER50yZ4pkzQgQYKlEEMmKICQ8Gk5Gx3W//c47FpzLsWCho+V4eDSNa6eOm1AbFhY5Catp/v0aA5FpdCZWrq9BmDmwBcWpg+TtxwjSBGVxOdvr4cn2eXrTlshWrVrVN5uxpbihh0fF0ofPGaix26cSUuBUQioPoBkzZt6fPHXK396gD0B9smiREws5Gc3H0ydMZKHYj6urarkS0I36YGQYdP3nQ8SqwRZ+wUqwhhWVlPPm3svHj6nxLVevXt03GwNqxQoWicGUI1Ox9//8wSz8q+PF0aO7x4wZ043jN2nOS2N4WuWyBP2MPmeMeP55NmvKFE6wVEeaqsH1rIQGrEfjKvYfQrGtgLD60OEAAAAASUVORK5CYII="}')

    def test_parse_team_with_no_avatar(self):
        with open('test_data/fms_api/2018_avatars_frc1.json', 'r') as f:
            models, more_pages = FMSAPITeamAvatarParser(2018).parse(json.loads(f.read()))

            self.assertFalse(more_pages)
            self.assertEqual(len(models), 1)

            # Ensure we get the proper Media model back
            media = models[0]
            self.assertEqual(media.key, ndb.Key('Media', 'avatar_avatar_2018_frc1'))
            self.assertEqual(media.foreign_key, 'avatar_2018_frc1')
            self.assertEqual(media.media_type_enum, MediaType.AVATAR)
            self.assertEqual(media.references, [ndb.Key('Team', 'frc1')])
            self.assertEqual(media.year, 2018)
            self.assertEqual(media.details_json, '{"base64Image": null}')

    def test_parse_result_with_multiple_teams(self):
        with open('test_data/fms_api/2018_avatars_multiple.json', 'r') as f:
            models, more_pages = FMSAPITeamAvatarParser(2018).parse(json.loads(f.read()))

            self.assertFalse(more_pages)
            self.assertEqual(len(models), 2)

            # Ensure we get the proper Media model back
            media_team_1 = models[0]
            self.assertEqual(media_team_1.key, ndb.Key('Media', 'avatar_avatar_2018_frc1'))
            self.assertEqual(media_team_1.foreign_key, 'avatar_2018_frc1')
            self.assertEqual(media_team_1.media_type_enum, MediaType.AVATAR)
            self.assertEqual(media_team_1.references, [ndb.Key('Team', 'frc1')])
            self.assertEqual(media_team_1.year, 2018)
            self.assertEqual(media_team_1.details_json, '{"base64Image": null}')

            media_team_1741 = models[1]
            self.assertEqual(media_team_1741.key, ndb.Key('Media', 'avatar_avatar_2018_frc1741'))
            self.assertEqual(media_team_1741.foreign_key, 'avatar_2018_frc1741')
            self.assertEqual(media_team_1741.media_type_enum, MediaType.AVATAR)
            self.assertEqual(media_team_1741.references, [ndb.Key('Team', 'frc1741')])
            self.assertEqual(media_team_1741.year, 2018)
            self.assertEqual(media_team_1741.details_json, '{"base64Image": "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"}')
