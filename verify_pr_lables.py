#!/usr/bin/env python3

import os
import sys
import re
from github import Github


def get_env_var(env_var_name, echo_value=False):
    """Try to get the value from a environmental variable.

    If the values is 'None', then a ValueError exception will
    be thrown.

    Args
    ----
    env_var_name : str
        The name of the environmental variable.
    echo_value : bool, optional, default False
        Print the resulting value.

    Returns
    -------
    value : str
        The value from the environmental variable.

    """
    value = os.environ.get(env_var_name)

    if value is None:
        print(f'ERROR: The environmental variable {env_var_name} is empty!',
              file=sys.stderr)
        sys.exit(1)

    if echo_value:
        print(f"{env_var_name} = {value}")

    return value


token = sys.argv[1]
if not token:
    print('ERROR: A token must be provided!', file=sys.stderr)
    sys.exit(1)

# Get the list of valid labels
valid_labels = [label.strip() for label in sys.argv[2].split(',')]
print(f'Valid labels are: {valid_labels}')

# Get the PR number
pr_number_str = sys.argv[3]

# Get needed values from the environmental variables
repo_name = get_env_var('GITHUB_REPOSITORY')
github_ref = get_env_var('GITHUB_REF')
github_event_name = get_env_var('GITHUB_EVENT_NAME')

# Create a repository object, using the GitHub token
repo = Github(token).get_repo(repo_name)

# When this actions runs on a "pull_reques_target" event, the pull request
# number is not available in the environmental variables; in that case it must
# be defined as an input value. Otherwise, we will extract it from the
# 'GITHUB_REF' variable.
if github_event_name == 'pull_request_target':
    # Verify the passed pull request number
    try:
        pr_number = int(pr_number_str)
    except ValueError:
        print('ERROR: A valid pull request number input must be defined when '
              'triggering on "pull_request_target". The pull request number '
              'passed was "{pr_number_str}".',
              file=sys.stderr)
        sys.exit(1)
else:
    # Try to extract the pull request number from the GitHub reference.
    try:
        pr_number = int(re.search('refs/pull/([0-9]+)/merge',
                        github_ref).group(1))
    except AttributeError:
        print('ERROR: The pull request number could not be extracted from '
              f'GITHUB_REF = "{github_ref}"', file=sys.stderr)
        sys.exit(1)

print(f'Pull request number: {pr_number}')

# Create a pull request object
pr = repo.get_pull(pr_number)

# Check if the PR comes from a fork. If so, the trigger must be
# 'pull_request_target'. Otherwise exit on error here.
# if pr.head.repo.full_name != pr.base.repo.full_name:
#     if github_event_name != 'pull_request_target':
#         print('ERROR: PRs from forks are only supported when trigger on '
#               '"pull_request_target"', file=sys.stderr)
#         sys.exit(1)

comments = pr.get_issue_comments()
message = sys.argv[4]
message_posted = any(comment.body == message for comment in comments)

# Get the pull request labels
pr_labels = pr.get_labels()

# Get the list of reviews
pr_reviews = pr.get_reviews()

# This is a list of valid labels found in the pull request
pr_valid_labels = []

# Check which of the label in the pull request, are in the
# list of valid labels
for label in pr_labels:
    if label.name in valid_labels:
        pr_valid_labels.append(label.name)


# Check if there were not invalid labels and at least one valid label.
#
# Note: When reviews are enabled, we always exit without an error code and let
# the check to succeed. Instead, we will create a pull request review, marked
# with 'REQUEST_CHANGES' when no valid label or invalid labels are found.
# This will prevent merging the pull request. When a valid label and not
# invalid labels are found, we will create a new pull request review, but in
# this case marked as 'APPROVE'. This will allow merging the pull request.
#
# Note 2: When reviews are enabled, we check for the status of the previous
# review done by this module. If a previous review exists, and it state and
# the current state are the same, a new request won't be generated.
#
# Note 3: We want to generate independent reviews for both cases: an invalid
# label is present and a valid label is missing.
#
# Note 4: If reviews are disabled, we do not generate reviews. Instead, we exit
# with an error code when no valid label or invalid labels are found, making
# the check fail. This will prevent merging the pull request. When a valid
# label and not invalid labels are found, we exit without an error code,
# making the check pass. This will allow merging the pull request.

# Then, we check it there are valid labels, and generate comment if needed,
# or exit with an error code. This is done independently of the presence of
# invalid labels above.
if not pr_valid_labels:
    print('Error! This pull request does not contain any of the valid labels: '
          f'{valid_labels}', file=sys.stderr)

    if not message_posted:
        # pr.create_issue_comment(message)
        pr.create_issue_comment(message.format(", ".join(valid_labels)))
    # If reviews are disable, exit with an error code.
    print('Exiting with an error code')
    sys.exit(1)

else:
    print('This pull request contains the following valid labels: '
          f'{pr_valid_labels}')
