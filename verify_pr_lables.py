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
        print(
            f"ERROR: The environmental variable {env_var_name} is empty!",
            file=sys.stderr,
        )
        sys.exit(1)

    if echo_value:
        print(f"{env_var_name} = {value}")

    return value


token = sys.argv[1]
if not token:
    print("ERROR: A token must be provided!", file=sys.stderr)
    sys.exit(1)

# Get the list of valid labels
valid_labels = [label.strip() for label in sys.argv[2].split(",")]
print(f"Valid labels are: {valid_labels}")

# Get the PR number
pr_number_str = sys.argv[3]

# Get needed values from the environmental variables
repo_name = get_env_var("GITHUB_REPOSITORY")
github_ref = get_env_var("GITHUB_REF")
github_event_name = get_env_var("GITHUB_EVENT_NAME")

# Create a repository object, using the GitHub token
repo = Github(token).get_repo(repo_name)

if github_event_name == "pull_request_target":
    # Verify the passed pull request number
    try:
        pr_number = int(pr_number_str)
    except ValueError:
        print(
            "ERROR: A valid pull request number input must be defined when "
            'triggering on "pull_request_target". The pull request number '
            'passed was "{pr_number_str}".',
            file=sys.stderr,
        )
        sys.exit(1)
else:
    # Try to extract the pull request number from the GitHub reference.
    try:
        pr_number = int(
            re.search("refs/pull/([0-9]+)/merge", github_ref).group(1)
        )
    except AttributeError:
        print(
            "ERROR: The pull request number could not be extracted from "
            f'GITHUB_REF = "{github_ref}"',
            file=sys.stderr,
        )
        sys.exit(1)

pr = repo.get_pull(pr_number)

message = sys.argv[4].format(", ".join(valid_labels))
message_posted = any(
    comment.body == message for comment in pr.get_issue_comments()
)


# This is a list of valid labels found in the pull request
pr_valid_labels = [
    label for label in pr.get_labels() if label.name in valid_labels
]


if not pr_valid_labels:
    print(
        "Error! This pull request does not contain any of the valid labels: "
        f"{valid_labels}",
        file=sys.stderr,
    )

    if not message_posted:
        pr.create_issue_comment(message)
    # If reviews are disable, exit with an error code.
    print("Exiting with an error code")
    sys.exit(1)

else:
    print(
        "This pull request contains the following valid labels: "
        f"{pr_valid_labels}"
    )
