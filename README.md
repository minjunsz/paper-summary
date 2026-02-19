# Paper Summary AI Workflow

## User Story

1. prompt with arxiv link
    1. User gives an arxiv link (e.g. `https://arxiv.org/abs/2602.16705`) or arxiv ID (e.g. `2602.16705`).
    2. The program automatically downloads the pdf file and parse it into text.
    3. LLM with openrouter will be used to summarize the paper.
       1. First, generate a thorough paper analysis using `arcee-ai/trinity-large-preview:free` model, covering: tackling problem, core idea, key contributions, methodologies, analysis/limitations, and other noteworthy points.
       2. Then, translate the detailed analysis to Korean using `arcee-ai/trinity-large-preview:free`. Keep technical terminologies in English, translate all other terms to Korean.
       3. Finally, summarize the translated detailed analysis into 3 lines and brief bullet points using `arcee-ai/trinity-mini:free` model.
2. More user stories will be added later.

## How LLM should works

Openrouter API key will be provided by .env file.

### Paper summary

1. Make a thorough paper analysis which does not miss any of these details using `arcee-ai/trinity-large-preview:free` model.
    - tackling problem (limitations of previous methods)
    - core idea
    - key contributions
    - methodologies (including details)
    - analysis or limitations
    - any other paper specific noteworthy points
2. Translate the detailed analysis to Korean using `arcee-ai/trinity-large-preview:free`. Keep technical terminologies in English, translate all other terms to Korean.
3. summarize the translated detailed analysis into 3 lines with `arcee-ai/trinity-mini:free` model.
4. summarize the translated detailed analysis into brief summary using bullet points with `arcee-ai/trinity-mini:free` model.

All three results (detailed analysis in Korean, 3 lines summary, and bullet-point summary) should be written in Korean (except technical terminologies).

## UI Requirements

1. When the user enter the arxiv link or ID, user should check the metadata of the paper, so that users can verify they prompted the right paper before running the LLM.
2. The process of the paper summary workflow (download -> text parse -> detailed summary -> 3-line / bullet-point summary) should be visible to the user.
3. Error messages for each step should be visible and proper retry logic should be provided.
4. The UI should be reactive even when the server is processing the data.
5. The summarized paper should be saved into a DB so that user can retrieve the three results once they summarize a paper. (sqlite might be enough)
6. User can see all three types of results (at first, 3-line summary is only visible, and if the user clicks buttons, tabs, or accordians, the rest are shown.)

