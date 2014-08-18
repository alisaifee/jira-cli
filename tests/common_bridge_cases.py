"""

"""
import os
import vcr

jiravcr = vcr.VCR(
    record_mode = 'once',
    match_on = ['uri', 'method'],
)

class BridgeTests:
    def test_get_issue(self):
        with jiravcr.use_cassette(os.path.join(self.vcr_directory, "issue.yaml")):
            self.assertIsNotNone(self.bridge.get_issue("TP-9"))

    def test_get_statuses(self):
        with jiravcr.use_cassette(os.path.join(self.vcr_directory, "status.yaml")):
            self.assertIsNotNone(self.bridge.get_statuses())

    def test_get_projects(self):
        with jiravcr.use_cassette(os.path.join(self.vcr_directory, "project.yaml")):
            self.assertIsNotNone(self.bridge.get_projects())

    def test_get_priorities(self):
        with jiravcr.use_cassette(
                os.path.join(self.vcr_directory, "priorities.yaml")):
            self.assertIsNotNone(self.bridge.get_priorities())

    def test_get_transitions(self):
        with jiravcr.use_cassette(
                os.path.join(self.vcr_directory, "transitions.yaml")):
            self.assertIsNotNone(self.bridge.get_available_transitions("TP-9"))

    def test_get_resolutions(self):
        with jiravcr.use_cassette(
                os.path.join(self.vcr_directory, "resolutions.yaml")):
            self.assertIsNotNone(self.bridge.get_resolutions())

    def test_get_project_components(self):
        with jiravcr.use_cassette(
                os.path.join(self.vcr_directory, "components.yaml")):
            self.assertIsNotNone(self.bridge.get_components("TP"))

    def test_get_issue_types(self):
        with jiravcr.use_cassette(os.path.join(self.vcr_directory, "types.yaml")):
            self.assertIsNotNone(self.bridge.get_issue_types())

    def test_get_sub_task_issue_types(self):
        with jiravcr.use_cassette(
                os.path.join(self.vcr_directory, "subtypes.yaml")):
            self.assertIsNotNone(self.bridge.get_issue_types())

    def test_get_filters(self):
        with jiravcr.use_cassette(os.path.join(self.vcr_directory, "filters.yaml")):
            self.assertIsNotNone(self.bridge.get_filters())

    def test_search_free_text(self):
        with jiravcr.use_cassette(os.path.join(self.vcr_directory, "search.yaml")):
            self.assertTrue(
                len(
                    self.bridge.search_issues("test jira-cli")
                ) == 1)

    def test_search_jql(self):
        with jiravcr.use_cassette(
                os.path.join(self.vcr_directory, "search-jql.yaml")):
            self.assertTrue(
                len(
                    self.bridge.search_issues_jql("summary~jira-cli")
                ) == 1)

    def test_filter_fail(self):
        with jiravcr.use_cassette(
                os.path.join(self.vcr_directory, "filter-search-fail.yaml")):
            self.assertIsNotNone(
                self.bridge.get_issues_by_filter("test-filter")
            )

    def test_filter_fail(self):
        with jiravcr.use_cassette(
                os.path.join(self.vcr_directory, "filter-search.yaml")):
            self.assertIsNotNone(
                self.bridge.get_issues_by_filter("test filter", "blah")
            )

    def test_create_issue(self):
        with jiravcr.use_cassette(os.path.join(self.vcr_directory, "create.yaml")):
            self.assertIsNotNone(
                self.bridge.create_issue("TP", summary='test-create-issue')
            )

    def test_create_child_issue(self):
        with jiravcr.use_cassette(
                os.path.join(self.vcr_directory, "childcreate.yaml")):
            self.assertIsNotNone(
                self.bridge.create_issue("TP", type='sub-task',
                                         summary='test-create-issue',
                                         parent='TP-10')
            )