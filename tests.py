#
# Tests
#

import unittest
import os

import munkistaging.default_settings as default_settings
from munkistaging.config import MunkiStagingConfig

from dateutil import parser 

FULL_TESTS=0
if os.environ.has_key('FULL_TESTS'):
    FULL_TESTS=1

class ScheduleTests(unittest.TestCase):

    def setUp(self):
        self.config = MunkiStagingConfig()
        self.config.cli_parse() # Um ....
        self.config.read_config([ 'test-data/schedule.cfg' , ])

    def testconfigloaded(self):
        self.failUnless( self.config.has_section('schedule_test') )

    def test_none_returned_with_no_config(self):

        autoschedule = self.config.autostage_schedule()
        self.assertIsNone(autoschedule)

        autoschedule = self.config.autostage_schedule('this_does_not_exist')
        self.assertIsNone(autoschedule)

    def test_schedule_standard(self):
        self.test = self.config.autostage_schedule('test')
        self.assertIsNotNone(self.test)
        # Um ...
        should_not_stage = [
                         parser.parse('2014-10-06 08:00:01'), # Monday
                         parser.parse('2014-10-06 08:30'),
                         parser.parse('2014-10-06 08:59:59'),
                         parser.parse('2014-10-06 10:01'),
                         parser.parse('2014-10-06 11:15'),
                         parser.parse('2014-10-06 12:27'),
                         parser.parse('2014-10-06 13:59'),
                         parser.parse('2014-10-07 07:45'),     # Tuesday
                         parser.parse('2014-10-07 07:59:59'),
                         parser.parse('2014-10-07 08:30:01'),
                         parser.parse('2014-10-07 14:23'),
                         parser.parse('2014-10-07 18:35'),
                         parser.parse('2014-10-08 00:00:1'),     # Wednesday
                         parser.parse('2014-10-08 02:15'),
                         parser.parse('2014-10-08 15:46'),
                         parser.parse('2014-10-08 19:21'),
                         parser.parse('2014-10-08 23:59:59'),
                         parser.parse('2014-10-09 03:33:45'),     # Thursday
                         parser.parse('2014-10-09 04:55'),
                         parser.parse('2014-10-09 06:09'),
                         parser.parse('2014-10-09 22:00:00'),
                         parser.parse('2014-10-10 16:23:00'),     # Friday
                         parser.parse('2014-10-10 07:58:02'),
                         parser.parse('2014-10-10 05:08:43'),
                         parser.parse('2014-10-10 08:35:00'),
                         parser.parse('2014-10-04 07:59:59'),  # Sunday
                         parser.parse('2014-10-04 08:30:05'),
                         parser.parse('2014-10-04 21:30:05'),
                         parser.parse('2014-10-04 20:52'),
                         parser.parse('2014-10-05 01:04:04'),  # Saturday
                         parser.parse('2014-10-05 17:11'),
                         parser.parse('2014-10-05 13:47'),
        ]
        should_stage = [ parser.parse('2013-05-20 00:00'), # Monday
                         parser.parse('2013-05-20 00:00:01'),
                         parser.parse('2013-05-20 03:00'),
                         parser.parse('2013-05-20 07:59:59'),
                         parser.parse('2013-05-20 09:00:01'),
                         parser.parse('2013-05-20 09:54'),
                         parser.parse('2013-05-20 09:59:59'),
                         parser.parse('2013-05-21 08:00'), # Tuesday
                         parser.parse('2013-05-21 08:02'),
                         parser.parse('2013-05-21 08:17'),
                         parser.parse('2013-05-21 08:22'),
                         parser.parse('2013-05-21 08:29:59'),
                         parser.parse('2013-05-21 08:30'),
                         parser.parse('2013-05-24 08:00'), # Friday
                         parser.parse('2013-05-24 08:29:59'),
                         parser.parse('2013-05-24 08:30'),
                         parser.parse('2013-05-26 08:00:01'), # Sunday
                         parser.parse('2013-05-26 08:10'),
                         parser.parse('2013-05-26 08:29:59'),
        ]

        for test_time in should_not_stage:
            self.assertFalse( self.test.stage_now(test_time),
                              msg='Should not be staging at %s' % test_time )

        for test_time in should_stage:
            self.assertTrue( self.test.stage_now(test_time),
                              msg='Should be staging at %s' % test_time )

    def test_schedule_short(self):
        self.short = self.config.autostage_schedule('short')
        self.assertIsNotNone(self.short)
        for sec in range(0,60):
            test_time = parser.parse('2012-12-07 09:00:%s' % sec)
            self.assertTrue( self.short.stage_now(test_time),
                              msg='Should be staging at %s' % test_time)

        for sec in range(1,60):
            test_time = parser.parse('2012-12-07 09:01:%s' % sec)
            self.assertFalse( self.short.stage_now(test_time),
                              msg='Should be staging at %s' % test_time )
     
        for sec in range(0,60):
            test_time = parser.parse('2012-12-07 08:59:%s' % sec)
            self.assertFalse( self.short.stage_now(test_time),
                              msg='Should be staging at %s' % test_time )

    def test_wrong_end(self):
        self.assertRaises(ValueError, self.config.autostage_schedule, 'wrong_end')
    def test_before_start(self):
        self.assertRaises(ValueError, self.config.autostage_schedule, 'end_before_start')

    # Empty sections mean stage never
    @unittest.skipIf(FULL_TESTS==0,
        'Skipping slow test as FULL_TESTS is 0; set environment variabel FULL_TESTS to perform')
    def test_empty(self):
        empty = self.config.autostage_schedule('empty')
        self.assertIsNotNone(empty)

        for day in range(1,7):
            for hour in range(0,23):
                for min in range(0,59):
                    for sec in range(0,59):
                        test_time = parser.parse('2007-01-%s %s:%s:%s'
                                                 % (day, hour, min,sec) )
                        self.assertFalse( empty.stage_now(test_time),
                                     msg='Should not be staging at %s' % test_time)

    @unittest.skipIf(FULL_TESTS==0,
        'Skipping slow test as FULL_TESTS is 0; set environment variabel FULL_TESTS to perform')
    def test_full(self):
        always = self.config.autostage_schedule('always')
        self.assertIsNotNone(always)

        for day in range(1,7):
            for hour in range(0,23):
                for min in range(0,59):
                    for sec in range(0,59):
                        test_time = parser.parse('2007-01-%s %s:%s:%s'
                                                 % (day, hour, min,sec) )
                        self.assertTrue( always.stage_now(now=test_time),
                                     msg='Should not be staging at %s' % test_time)

if __name__ == '__main__':
    unittest.main()

