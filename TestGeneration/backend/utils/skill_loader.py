import os


def load_skill(name):
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents", "skills")
    fpath = os.path.join(skills_dir, f"{name}.skill.md")
    if os.path.isfile(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()
    return f"# {name}\n\nYou are an AI agent specializing in {name.replace('_', ' ')}."


def render_skill(name, **kwargs):
    content = load_skill(name)
    try:
        return content.format(**kwargs)
    except KeyError:
        return content
