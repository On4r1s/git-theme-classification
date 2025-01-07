# git-theme-classification

Short code to automatically assign general themes among all wiki pages(except home and Index-AI) and giving them small capture.

Topics are stored in index-ai wiki page.

## Preparing
To run, install all dependencies with

` pip install -r requirements.txt `

then, you need to insert envirement variables, such as:

- GPT API key
- gitlab API token
- gitlab project name
- max amount of themes

It can be done easily in IDE, or just changing code a little.

## Usage

Now u can simply run the script.

By default buffer is 5, so time needed to analize all wiki pages is ~ (wiki pages/5)+1 minutes.

You can see progress on your Index-AI page.
