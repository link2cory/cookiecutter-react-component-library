import os, subprocess

# cookiecutter jinja2 obj is extracted as an OrderedDict
from collections import OrderedDict
from cookiecutter.main import cookiecutter
from github import Github
from git import Repo

def setup_git(): 
    # activate .gitignore. It must be stored this way to facilitate versioning of
    # the cookiecutter.
    os.rename('gitignore', '.gitignore')

    # initialize local repo
    print('initializing local repository...')
    local = Repo.init(os.getcwd())
    local.git.add(A=True)
    local.index.commit('Initial Commit, project generated with cookiecutter-jam-app')
    print('done initializing local repository')


    if context['use_github'] == 'yes':
        print('setting up github repository...')
        remote = setup_remote(local)
        add_remote(local)
        print('done setting up github repository')
        
        if context['continuous_integration'] != 'no':
            print('setting up continuous integration...')
            setup_continuous_integration(local, remote)
            print('done setting up continuous integration...')

        if context['use_gitflow'] == 'yes':
            print('setting up gitflow...')
            setup_gitflow(remote)
            print('done setting up gitflow...')



def setup_remote(local):
    # create the github repo
    return Github('{{ cookiecutter.github_token }}').get_user().create_repo('{{ cookiecutter.project_slug }}')

def setup_gitflow(remote):
    # create the develop branch
    develop_branch = remote.create_git_ref(
        ref='refs/heads/develop',
        sha=remote.get_branch('master').commit.sha
    )

    # develop will be the default branch
    remote.edit(default_branch='develop')


def setup_continuous_integration(local, remote):
    ci_context = {"test_name": "{{ cookiecutter.ci_test_name }}"}

    # add the CI files from the template
    success = cookiecutter(
        context['ci_template'],
        extra_context=ci_context,
        no_input=True
    )

    # commit the CI files
    local.git.add(A=True)
    local.index.commit('Added Continuous Integration Support')

    # the default branch should be protected against pull requests that fail CI tests
    remote.get_branch(remote.default_branch).edit_protection(
            strict=True,
            contexts=['{{ cookiecutter.ci_test_name }}']
        )

def add_remote(local):
    # point local repo to the remote
    remote_repo = local.create_remote(
        'origin',
        'git@github.com:{{ cookiecutter.github_user }}/{{ cookiecutter.project_slug }}.git'
    )

    #  push to the remote
    remote_repo.push(refspec='{}:{}'.format('master', 'master'))

def remove_extra_files():
    # Remove github actions files unless they are necessary
    if context['use_github'] == 'no' or context['continuous_integration'] != 'github_actions':
        # remove the github directory
        os.rmtree('.github/')


# extract the context from the cookiecutter jinja2 obj
# it is much easier to work with this way...
context = {{ cookiecutter }}

# run cookiecutter for each sub-package
print('rendering subpackages...')
for name, package in context['packages'].items():
    print(f'rendering package: {name}')
    # make sure that the dependencies for this package don't get installed yet
    package_context = package['context']
    package_context['is_subpackage'] = True

    success = cookiecutter(
        package['template'],
        output_dir='packages',
        extra_context=package_context,
        no_input=True
    )
    print(f'finished rendering package: {name}')

print('finished rendering subpackages')

if context['is_subpackage'] == 'no':
  if context['install_dependencies'] == 'yes':
      print('installing dependencies...')
      subprocess.run(['yarn', 'install'])
      print('finished installing dependencies')

  if context['use_git'] == 'yes':
      print('setting up git...')
      setup_git()
      print('finished setting up git...')

