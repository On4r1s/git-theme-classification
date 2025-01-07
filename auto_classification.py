import json
import os
import time

import gitlab
import openai
from openai import OpenAI


def gpt_request(prompt):
    request = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": [{"type": "text", "text": prompt}]}],
        stream=True
    )
    answer = ""
    for chunk in request:
        if chunk.choices[0].delta.content is not None:
            answer += chunk.choices[0].delta.content
    return answer


def main():
    pages = {}
    is_wiki = False
    for wiki in project.wikis.list(iterator=True):
        b = json.loads(project.wikis.get(wiki.slug).to_json())
        if b['title'] != 'home' and b['title'] != "AI_Index":
            pages[b['title']] = {'title': b['title'], 'content': b['content'], 'slug': b['slug']}
        elif b['title'] == "AI_Index":
            is_wiki = True

    print('Done reading all wikis')

    if not is_wiki:
        project.wikis.create({"title": "AI_Index", "content": "WIP"})
        print('created wiki')

    # m służy jako ograniczenie buforu artykułów do analizy przez LLM w 1 zapytaniu, teoretycznie można zwiększyć
    m = 5
    generated = []
    titles_glob = []
    content = "# WIP\n\n"

    while True:
        try:
            prompt_capture = """Dalej jest podana informacja z tytułami artykułów i ich zawartością, przeanalizuj ich, napisz krótkie streszczenie, 2-3 zdania, żeby zachęcić do przeczytania całego artykułu. Na wyjściu masz zwrócić jedynie JSON w takiej postaci, nie zamieniając podanego tytułu, w zależności od ilości artykułów: {"tytuł_1": "streszczenie_1", "tytuł_2": "streszczenie_2"} i nic poza tym\n"""

            titles_loc = []
            for i in range(len(generated), len(generated) + m):
                try:
                    t, c, _ = list(pages.values())[i].values()
                    titles_loc.append(t)
                    prompt_capture += f""""{t}": "{c}"\n\n"""
                except IndexError:
                    break

            ans = gpt_request(prompt_capture)

            # czasami gpt zwraca JSON w formacie dla JS-a, więc to jest obejście takiej sytuacji
            try:
                new_list = list(json.loads(ans[7:-4]).values())
            except json.decoder.JSONDecodeError:
                new_list = list(json.loads(ans).values())

            for i in range(len(new_list)):
                content += f"<details><summary>[{pages[titles_loc[i]]['title']}](/{pages[titles_loc[i]]['slug']})</summary>{new_list[i]}</details>\n\n"
            project.wikis.update('AI_Index', {'content': content})
            generated.extend(new_list)

            if len(generated) == len(pages):
                print('Ended analyzing wikis')
            else:
                print(f'Analyzed {len(generated)}/{len(pages)} wikis')

            time.sleep(55)
            m = 5
            titles_glob.extend(titles_loc)

        except openai.RateLimitError:
            m -= 1

        except json.decoder.JSONDecodeError:
            print('Error:\n')
            print(ans)

        if len(generated) == len(pages):
            break

    to_send = {}
    for i in range(len(generated)):
        to_send[i] = generated[i]

    prompt_group = (f"""Dalej jest podany dict pythona z streszczeniami artykułów, przeanalizuj ich, pogrupuj na {group_count} grup lub mniej, wszystkie artykuły są tak czy inaczej związane z AI, więc grupuj ich po temacie. Nie zmieniaj ID. Nazwa grupy np. 'Generowanie obrazków', 'Analiza tekstu'. Na wyjściu masz zwrócić jedynie JSON w takiej postaci, w zależności od ilości artykułów i grup: _"nazwa grupy1": ["id artykułu1", "id artykułu2"]+ i nic poza tym\nJson: """
                        .replace('_', '{').replace('+', '}') + str(to_send))

    output = """## raporty

Tutaj powinny zostać dołączone raporty z Waszej pracy. Na tej stronie proszę wstawiać tylko linki do podstron wiki. Wszystkie materiały mają być w całości umieszczone w tym repozytorium (tekst, obrazki, audio, filmy). Proszę nie przesadzać z wielkością plików.

* przykładowa grupa **tworzenie gier**
  * [pong](pong-moj-projket)
  * snake
  * doom
  * CP2077\n\n"""

    answer = gpt_request(prompt_group)
    try:
        new_dict = json.loads(answer[7:-4])
    except json.decoder.JSONDecodeError:
        new_dict = json.loads(answer)


    for k, v in new_dict.items():
        output += f'* grupa **{k}**\n'
        for i in v:
            output += f"  <details><summary>[{pages[titles_glob[int(i)]]['title']}](/{pages[titles_glob[int(i)]]['slug']})</summary>{generated[int(i)]}</details>\n\n"

    project.wikis.update('AI_Index', {'content': output})
    print('Done!')


if __name__ == "__main__":

    # zmienne, można zmienić wszystkie na środowiskowe, lub z pliku .env

    gl = gitlab.Gitlab(url="https://gitlab.tele.agh.edu.pl", private_token=os.getenv('ACCESS_TOKEN'))

    project = gl.projects.get(os.getenv('PROJECT'))

    group_count = os.getenv('GROUP_COUNT')

    client = OpenAI(api_key=os.getenv('API_KEY'))

    main()
