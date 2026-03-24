import responses
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from raportointi.constants import VALSSI_PERMISSION_LEVELS, VALSSI_PAAKAYTTAJA_LEVEL, USER_PERMISSIONS_RECHECK_TIME
from raportointi.migrations.testing.setup import add_testing_responses_kayttooikeus_userauthorization
from raportointi.models import UserAuthorization
from raportointi.utils import (
    datenow_delta, get_valssi_permission_levels, get_valssi_organisaatiot_permissions,
    is_expired, transform_tuples_lists_to_integers, convert_lists_to_percent, convert_lists_to_sum,
    convert_lists_to_bool_with_limit, convert_lists_to_average, insert_line_breaks, get_henkilo_oid_and_permissions)
from raportointi.utils_datacollection import calculate_pct


class HelperFunctionsTests(TestCase):
    """Test helper functions in raportointi.utils"""

    def test_datenow_delta_gt(self):
        """Check current date greater than n days"""
        time_now = timezone.now()
        self.assertTrue(datenow_delta(2) > time_now)

    def test_datenow_delta_lt(self):
        """Check current date less than -n days"""
        time_now = timezone.now()
        self.assertTrue(datenow_delta(-2) < time_now)

    def test_calculate_pct_two_decimals(self):
        """Check calculation with max 2 decimals"""
        self.assertEqual(calculate_pct(2, 3), 67)
        self.assertEqual(calculate_pct(3, 2), 150)
        self.assertEqual(calculate_pct(3, 0), 0)
        self.assertEqual(calculate_pct(0, 3), 0)

    def test_past_current_date(self):
        """Test past_current_date function"""
        self.assertEqual(is_expired(datenow_delta(1).date()), False)
        self.assertEqual(is_expired(datenow_delta(0).date()), False)
        self.assertEqual(is_expired(datenow_delta(-1).date()), True)


class TransformTuplesListsToIntegersTest(TestCase):
    """Test helper functions in raportointi.utils used in view_report"""
    def test_transform_tuples_lists_to_integers(self):
        answers_lists_raw = [[(1, 5), (3, 1)], [(1, 2), (2, 2), (3, 2), (4, 2), (5, 2)]]
        expected_output = [[5, 0, 1, 0, 0], [2, 2, 2, 2, 2]]
        list_length = 5
        result = transform_tuples_lists_to_integers(list_length, answers_lists_raw)
        self.assertEqual(result, expected_output)

    def test_transform_tuples_lists_to_integers_with_none_value(self):
        answers_lists_raw = [[(1, 5), (3, 1), (None, None)], [(1, 2), (2, 2), (3, 2), (4, 2), (5, 2)]]
        expected_output = [[5, 0, 1, 0, 0], [2, 2, 2, 2, 2]]
        list_length = 5
        result = transform_tuples_lists_to_integers(list_length, answers_lists_raw)
        self.assertEqual(result, expected_output)

    def test_transform_tuples_lists_to_integers_with_index_out_of_range(self):
        answers_lists_raw = [[(6, 5), (3, 1)], [(1, 2), (2, 2), (3, 2), (4, 2), (5, 2)]]
        expected_output = [[0, 0, 1, 0, 0], [2, 2, 2, 2, 2]]
        list_length = 5
        result = transform_tuples_lists_to_integers(list_length, answers_lists_raw)
        self.assertEqual(result, expected_output)


class ConvertListsToPercentTest(TestCase):
    def test_convert_lists_to_percent(self):
        lst = [[10, 20, 30], [40, 50, 60]]
        expected_output = [[17, 33, 50], [27, 33, 40]]
        result = convert_lists_to_percent(lst)
        self.assertEqual(result, expected_output)

    def test_convert_lists_to_percent_with_zero_total(self):
        lst = [[0, 0, 0], [0, 0, 0]]
        expected_output = [[0, 0, 0], [0, 0, 0]]
        result = convert_lists_to_percent(lst)
        self.assertEqual(result, expected_output)

    def test_convert_lists_to_percent_with_zero_values(self):
        lst = [[10, 0, 20], [30, 0, 40]]
        expected_output = [[33, 0, 67], [43, 0, 57]]
        result = convert_lists_to_percent(lst)
        self.assertEqual(result, expected_output)


class ConvertListsToSumTest(TestCase):
    def test_convert_lists_to_sum(self):
        lst = [[1, 2, 3], [4, 5, 6]]
        expected_output = [6, 15]
        result = convert_lists_to_sum(lst)
        self.assertEqual(result, expected_output)

    def test_convert_lists_to_sum_with_empty_list(self):
        lst = [[], []]
        expected_output = [0, 0]
        result = convert_lists_to_sum(lst)
        self.assertEqual(result, expected_output)

    def test_convert_lists_to_sum_with_negative_values(self):
        lst = [[-1, -2, -3], [4, 5, 6]]
        expected_output = [-6, 15]
        result = convert_lists_to_sum(lst)
        self.assertEqual(result, expected_output)


class ConvertListsToBoolWithLimitTest(TestCase):
    def test_convert_lists_to_bool_with_limit(self):
        lst = [[1, 2, 3], [4, 5, 6]]
        limit = 5
        expected_output = [True, True]
        result = convert_lists_to_bool_with_limit(lst, limit)
        self.assertEqual(result, expected_output)

    def test_convert_lists_to_bool_with_limit_with_empty_list(self):
        lst = [[], []]
        limit = 5
        expected_output = [False, False]
        result = convert_lists_to_bool_with_limit(lst, limit)
        self.assertEqual(result, expected_output)

    def test_convert_lists_to_bool_with_limit_with_negative_values(self):
        lst = [[-1, -2, -3], [4, 5, 6]]
        limit = 0
        expected_output = [False, True]
        result = convert_lists_to_bool_with_limit(lst, limit)
        self.assertEqual(result, expected_output)


class ConvertListsToAverageTest(TestCase):
    def test_convert_lists_to_average(self):
        lists = [[1, 2, 3], [4, 5, 6]]
        expected_output = ["2,3", "2,1"]
        result = convert_lists_to_average(lists)
        self.assertEqual(result, expected_output)

    def test_convert_lists_to_average_with_empty_list(self):
        lists = [[], []]
        expected_output = ["0", "0"]
        result = convert_lists_to_average(lists)
        self.assertEqual(result, expected_output)

    def test_convert_lists_to_average_with_zero_sum(self):
        lists = [[1, 0, 0], [0, 0, 0]]
        expected_output = ["1,0", "0"]
        result = convert_lists_to_average(lists)
        self.assertEqual(result, expected_output)


class InsertLineBreaksTest(TestCase):
    def test_insert_line_breaks(self):
        strings = ["This is a test string", "This is another test string"]
        max_line_length = 10
        max_words_per_line = 2
        expected_output = ["This is <br>a test <br>string ", "This is <br>another <br>test <br>string "]

        result = insert_line_breaks(strings, max_line_length, max_words_per_line)

        self.assertEqual(result, expected_output)

    def test_short_string(self):
        strings = ["This is a short string"]
        max_line_length = 20
        max_words_per_line = 5
        expected_output = ["This is a short <br>string "]

        result = insert_line_breaks(strings, max_line_length, max_words_per_line)

        self.assertEqual(result, expected_output)

    def test_max_line_length_short(self):
        strings = ["This is a test string", "This is another test string"]
        max_line_length = 4
        max_words_per_line = 2
        expected_output = ["This <br>is a <br>test <br>string ", "This <br>is <br>another <br>test <br>string "]

        result = insert_line_breaks(strings, max_line_length, max_words_per_line)

        self.assertEqual(result, expected_output)

    def test_max_words_per_line(self):
        strings = ["This is a test string", "This is another test string"]
        max_line_length = 20
        max_words_per_line = 1
        expected_output = ["This <br>is <br>a <br>test <br>string ", "This <br>is <br>another <br>test <br>string "]

        result = insert_line_breaks(strings, max_line_length, max_words_per_line)

        self.assertEqual(result, expected_output)


class PermissionFunctionsTests(TestCase):
    def test_get_valssi_permission_levels_higher_before(self):
        perms = [{"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[0]},
                 {"palvelu": "some", "oikeus": "some"},
                 {"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[1]}]
        self.assertEqual(get_valssi_permission_levels(perms), list(VALSSI_PERMISSION_LEVELS[0:2]))

    def test_get_valssi_permission_levels_higher_later(self):
        perms = [{"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[1]},
                 {"palvelu": "some", "oikeus": "some"},
                 {"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[0]}]
        self.assertEqual(get_valssi_permission_levels(perms), list(VALSSI_PERMISSION_LEVELS[0:2]))

    def test_get_valssi_permission_levels_none_perms(self):
        perms = [{"palvelu": "some", "oikeus": "some"}, {"palvelu": "some2", "oikeus": "some2"}]
        self.assertEqual(get_valssi_permission_levels(perms), [])

    def test_get_valssi_permission_levels_empty_list(self):
        self.assertEqual(get_valssi_permission_levels([]), [])

    def test_get_valssi_organisaatiot_permissions(self):
        orgs = [{"organisaatioOid": "test",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[0]}]}]
        org_perms = get_valssi_organisaatiot_permissions(orgs)
        self.assertEqual(org_perms, [{"organisaatioOid": "test", "valssiPermissions": [VALSSI_PERMISSION_LEVELS[0]]}])


class UserAuthorizationDbTests(TestCase):
    databases = ["default", "virkailijapalvelu"]

    @responses.activate
    def test_user_authorization_db(self):
        add_testing_responses_kayttooikeus_userauthorization(responses)

        # check UserAuthorization not found in db
        self.assertFalse(UserAuthorization.objects.filter(username="test-userauth").exists())

        oid_henkilo, org_perms = get_henkilo_oid_and_permissions("test-userauth")

        self.assertEqual(oid_henkilo, "test-oidUA")
        self.assertEqual(len(org_perms), 1)
        self.assertEqual(org_perms[0]["organisaatioOid"], "test-oidUAorg")
        self.assertEqual(org_perms[0]["valssiPermissions"], [VALSSI_PAAKAYTTAJA_LEVEL])

        # check UserAuthorization found in db after request
        user_auth = UserAuthorization.objects.filter(username="test-userauth").first()
        updated_time_orig = user_auth.updated_time
        self.assertEqual(user_auth.oid, "test-oidUA")
        self.assertEqual(user_auth.permissions[0]["organisaatioOid"], "test-oidUAorg")
        self.assertEqual(user_auth.permissions[0]["valssiPermissions"], [VALSSI_PAAKAYTTAJA_LEVEL])

        # check data is same as first time
        oid_henkilo, org_perms = get_henkilo_oid_and_permissions("test-userauth")
        self.assertEqual(oid_henkilo, "test-oidUA")
        self.assertEqual(len(org_perms), 1)
        self.assertEqual(org_perms[0]["organisaatioOid"], "test-oidUAorg")
        self.assertEqual(org_perms[0]["valssiPermissions"], [VALSSI_PAAKAYTTAJA_LEVEL])

        # check UserAuthorization not updated after (instant) new request
        user_auths = UserAuthorization.objects.filter(username="test-userauth")
        self.assertEqual(user_auths.count(), 1)
        user_auth = user_auths.first()
        self.assertEqual(user_auth.updated_time, updated_time_orig)

        # check UserAuthorization is updated after recheck-time (outdate time manually)
        outdated_time = timezone.now() - timedelta(minutes=USER_PERMISSIONS_RECHECK_TIME, seconds=1)
        UserAuthorization.objects.filter(id=user_auth.id).update(updated_time=outdated_time)
        get_henkilo_oid_and_permissions("test-userauth")
        user_auth = UserAuthorization.objects.filter(username="test-userauth").first()
        self.assertTrue(user_auth.updated_time > updated_time_orig)
