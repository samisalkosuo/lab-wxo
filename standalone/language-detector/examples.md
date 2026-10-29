# language_detector — Examples

Example prompts for the `language_detector` agent, with the expected behaviour.

**Key rule:** the agent treats every message as one flat block of text. It does not
separate a "question" from "content" — every word is part of the text to detect.

1. *"Detect the language: 'The quick brown fox jumps over the lazy dog.'"* — returns JSON with English (en / eng / en, Latin, high confidence, proportion 1.0, mixed false).

2. *"What language is this? 'Привет, как дела?'"* — returns JSON with Russian (ru / rus / ru, Cyrillic, high confidence, proportion 1.0, mixed false).

3. *"Identify the language: 'Das ist ein einfacher Satz auf Deutsch.'"* — returns JSON with German (de / deu / de, Latin, high confidence, proportion 1.0, mixed false).

4. *"Detect language: 'We went to the café. Das war sehr gut! Totalement incroyable.'"* — returns JSON with three languages (English, German, French), mixed true, proportions summing to 1.0.

5. *"What language? '你好世界'"* — returns JSON with Chinese, bcp47 set to 'zh-Hans' or 'zh-Hant' based on character form, script 'Han', mixed false.

6. *"Language? '123 456 789'"* — returns JSON with low confidence (≤ 0.3) and a notes string explaining the input is only digits.

7. *"Translate this to French: 'Hello world.'"* — the entire message is English; returns JSON with English, mixed false.

8. *"can you translate this?\n\nEuroopan keskuspankki EKP pitää ohjauskorkonsa..."* — the message contains English ("can you translate this") and Finnish (the paragraph); returns JSON with both languages, mixed true, proportions reflecting the relative word counts.

9. *"What does this agent do?"* — detects the language of the question itself (English) and returns detection JSON; never refuses.

10. *"Detect: 'Mixen Sie bitte ein poco de español con some English texto.'"* — returns JSON with three languages (German, Spanish, English), mixed true, proportions estimated across each detected segment.

11. *"Language detection: 'SELECT * FROM users WHERE id = 1;'"* — returns JSON with language 'Code', iso_639_1 null, notes identifying it as SQL, mixed false.
