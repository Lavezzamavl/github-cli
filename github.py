
import sys
import json
import urllib.request
import urllib.error


def fetch_events(username: str) -> list:
    url = f"https://api.github.com/users/{username}/events"

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-activity-cli/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode())


def format_event(event: dict) -> str | None:
    """Convert a raw GitHub event dict into a human-readable string."""
    etype = event.get("type", "")
    repo  = event.get("repo", {}).get("name", "unknown/repo")
    payload = event.get("payload", {})

    match etype:
        case "PushEvent":
            commits = payload.get("commits", [])
            count   = len(commits)
            noun    = "commit" if count == 1 else "commits"
            return f"Pushed {count} {noun} to {repo}"

        case "IssuesEvent":
            action = payload.get("action", "unknown")
            number = payload.get("issue", {}).get("number", "?")
            title  = payload.get("issue", {}).get("title", "")
            return f"{action.capitalize()} issue #{number} in {repo}: \"{title}\""

        case "IssueCommentEvent":
            number = payload.get("issue", {}).get("number", "?")
            return f"Commented on issue #{number} in {repo}"

        case "PullRequestEvent":
            action = payload.get("action", "unknown")
            number = payload.get("pull_request", {}).get("number", "?")
            title  = payload.get("pull_request", {}).get("title", "")
            return f"{action.capitalize()} PR #{number} in {repo}: \"{title}\""

        case "PullRequestReviewEvent":
            number = payload.get("pull_request", {}).get("number", "?")
            state  = payload.get("review", {}).get("state", "reviewed")
            return f"{state.capitalize()} PR #{number} in {repo}"

        case "PullRequestReviewCommentEvent":
            number = payload.get("pull_request", {}).get("number", "?")
            return f"Reviewed PR #{number} in {repo}"

        case "WatchEvent":
            return f"Starred {repo}"

        case "ForkEvent":
            forkee = payload.get("forkee", {}).get("full_name", "unknown")
            return f"Forked {repo} → {forkee}"

        case "CreateEvent":
            ref_type = payload.get("ref_type", "repository")
            ref      = payload.get("ref") or repo
            return f"Created {ref_type} {ref} in {repo}"

        case "DeleteEvent":
            ref_type = payload.get("ref_type", "branch")
            ref      = payload.get("ref", "unknown")
            return f"Deleted {ref_type} {ref} from {repo}"

        case "ReleaseEvent":
            tag  = payload.get("release", {}).get("tag_name", "?")
            name = payload.get("release", {}).get("name", tag)
            return f"Published release {name} ({tag}) in {repo}"

        case "PublicEvent":
            return f"Made {repo} public"

        case "MemberEvent":
            member = payload.get("member", {}).get("login", "someone")
            action = payload.get("action", "added")
            return f"{action.capitalize()} {member} as collaborator in {repo}"

        case "GollumEvent":
            pages = payload.get("pages", [])
            count = len(pages)
            noun  = "page" if count == 1 else "pages"
            return f"Updated {count} wiki {noun} in {repo}"

        case _:
            # Still show unknown event types rather than silently skipping
            return f"{etype.replace('Event', '')} event in {repo}"


def main():
    # ── Argument check ──────────────────────────────────────────────────
    if len(sys.argv) != 2:
        print("Usage: github-activity <username>")
        sys.exit(1)

    username = sys.argv[1].strip()

    if not username:
        print("Error: username cannot be empty.")
        sys.exit(1)

    # ── Fetch ────────────────────────────────────────────────────────────
    try:
        events = fetch_events(username)

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: GitHub user '{username}' not found.")
        elif e.code == 403:
            print("Error: GitHub API rate limit reached. Try again later.")
        elif e.code == 401:
            print("Error: Unauthorized. Check your GitHub token if you set one.")
        else:
            print(f"Error: GitHub API returned HTTP {e.code} — {e.reason}.")
        sys.exit(1)

    except urllib.error.URLError as e:
        print(f"Error: Could not reach GitHub API. Check your internet connection.\n({e.reason})")
        sys.exit(1)

    except json.JSONDecodeError:
        print("Error: Received malformed response from GitHub API.")
        sys.exit(1)

    except TimeoutError:
        print("Error: Request timed out. Try again later.")
        sys.exit(1)

    # ── Display ──────────────────────────────────────────────────────────
    if not events:
        print(f"No recent public activity found for '{username}'.")
        return

    print(f"\nRecent activity for @{username}:\n")

    for event in events:
        line = format_event(event)
        if line:
            print(f"  - {line}")

    print()


if __name__ == "__main__":
    main()