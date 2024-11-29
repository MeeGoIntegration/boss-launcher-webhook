from django.test import TestCase

from webhook_launcher.app.misc import normalize_git_url, giturlparse


class TestUrlFunc(TestCase):

    def test_normalize_git_url(self):
        mapping = [
            # input, output
            ('gl.com/prj/', 'git://gl.com/prj.git'),
            ('git://gl.com/prj.', 'git://gl.com/prj.git'),
            ('git://gl.com/prj/', 'git://gl.com/prj.git'),
            ('git://gl.com/prj//', 'git://gl.com/prj.git'),
            ('git://gl.com/prj.git', 'git://gl.com/prj.git'),
        ]
        for source, expect in mapping:
            self.assertEqual(normalize_git_url(source), expect)

    def test_giturlparse(self):
        mapping = [
            # input, output
            ('gl.com/prj/', 'git://gl.com/prj/'),
            ('git://gl.com/prj/', 'git://gl.com/prj/'),
            ('git://u:p@gl.com/prj.git', 'git://gl.com/prj.git'),
        ]
        for source, expect in mapping:
            self.assertEqual(
                giturlparse(source).geturl(),
                expect
            )
