from github import Github

g = Github( ${{Pygithub.secrets}} )

for repo in g.get_user().get_repos():
    print(repo.name)
