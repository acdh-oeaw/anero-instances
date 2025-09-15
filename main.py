#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "PyGithub",
#   "Jinja2",
#   "httpx",
#   "markdown",
# ]
# ///

import pathlib
import tomllib
import json
import markdown
import os
import random
from github import Github, Auth
from github.GithubException import UnknownObjectException
from jinja2 import Environment, FileSystemLoader
from dataclasses import dataclass, asdict, field


def markdownify(_input: str) -> str:
    return markdown.markdown(_input)


@dataclass
class Project:
    url: str
    github: dict = field(default_factory=dict)
    pyproject_toml: dict = field(default_factory=dict)
    readme: str = ""


def fetch_projects():
    projects = []
    projects_file = tomllib.loads(pathlib.Path("projects.toml").read_text())

    if token := os.getenv("GITHUB_TOKEN", False):
        print("Using authentication")
        auth = Auth.Token(token)
        g = Github(auth=auth)
    else:
        g = Github()
    for project in projects_file["projects"]:
        if project.startswith("https://github.com/"):
            repo = g.get_repo(project.replace("https://github.com/", ""))
            p = Project(github=repo.raw_data, url=project)
            try:
                pyproject_toml = repo.get_contents("pyproject.toml")
                p.pyproject_toml = tomllib.loads(
                    pyproject_toml.decoded_content.decode()
                )
                readme = repo.get_contents("README.md")
                p.readme = readme.decoded_content.decode()
            except UnknownObjectException:
                pass
            projects.append(p)

    return projects


def main():
    env = Environment(loader=FileSystemLoader("templates"))
    env.filters["markdownify"] = markdownify
    template = env.get_template("index.html")

    project_cache_file = pathlib.Path("project_cache.json")
    if project_cache_file.exists():
        projects = json.loads(project_cache_file.read_text())
    else:
        projects = fetch_projects()
        project_cache_file.write_text(
            json.dumps([asdict(project) for project in projects])
        )

    random.shuffle(projects)

    context = {"projects": projects}

    output = template.render(context)
    pathlib.Path("index.html").write_text(output)


if __name__ == "__main__":
    main()
