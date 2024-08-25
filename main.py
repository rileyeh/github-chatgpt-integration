import argparse
import openai
import os
import requests
from github import Github, PullRequest

github_client: Github
parameters: dict

def code_review(parameters: dict):
    repo = github_client.get_repo(os.getenv('GITHUB_REPOSITORY'))
    pull_request = repo.get_pull(parameters["pr_id"])

    commits = pull_request.get_commits()

    for commit in commits:
        files = commit.files

        for file in files:
            filename = file.filename
            content = repo.get_contents(filename, ref=commit.sha).decoded_content

            try:
                response = openai.ChatCompletion.create(
                    model=parameters['model'],
                    messages=[
                        {
                            "role" : "user",
                            "content" : (f"{parameters['prompt']}:\n```{content}```")
                        }
                    ],
                    temperature=parameters['temperature']
                )

                pull_request.create_issue_comment(f"Review for `{file.filename}` file:\n {response['choices'][0]['message']['content']}")
            except Exception as ex:
                message = f"🚨 Fail code review process for file **{filename}**.\n\n`{str(ex)}`"
                pull_request.create_issue_comment(message)


def make_prompt() -> str:
    review_prompt = f"You are a manager of a new hire who is submitting code for a project you're working on. You will be reviewing the new hire's code and giving feedback on how well the code aligns with the goal of the project as well as suggestions about their code and how to improve. You should give feedback on how well their code follows industry best practices. You should not give them the answers to any problems, but should point out where there is room for improvement and perhaps give advice on where to look, but do not give them the solution. Generate your response in markdown format"

    return review_prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--openai-api-key', help='Your OpenAI API Key')
    parser.add_argument('--github-token', help='Your Github Token')
    parser.add_argument('--github-pr-id', help='Your Github PR ID')
    parser.add_argument('--openai-engine', default="gpt-4o", help='GPT-4o model to use. Options: text-davinci-003, text-davinci-002, text-babbage-001, text-curie-001, text-ada-001')
    parser.add_argument('--openai-temperature', default=0.0, help='Sampling temperature to use. Higher values means the model will take more risks. Recommended: 0.5')
    parser.add_argument('--openai-max-tokens', default=4096, help='The maximum number of tokens to generate in the completion.')
    
    args = parser.parse_args()

    openai.api_key = args.openai_api_key
    github_client = Github(args.github_token)

    review_parameters = {
        "pr_id" : int(args.github_pr_id),
        "prompt" : make_prompt(),
        "temperature" : float(args.openai_temperature),
        "max_tokens" : int(args.openai_max_tokens),
        "model" : args.openai_engine
    }

    code_review(parameters=review_parameters)
