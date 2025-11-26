# ***Context Engineering***
---

This file serves as inspiration for context engneering techniques that are currently being used by experts in the industry.

***Inpsired by:***
- [Langchain](https://www.notion.so/Context-Engineering-for-Agents-2a1808527b17803ba221c2ced7eef508)
- [Video](https://www.youtube.com/watch?v=XFCkrYHHfpQ&t=217s)


## ***`What is context engineering?`***
`The art and science to fill the context with just the right information for the next step.`

[Chroma research](https://research.trychroma.com/context-rot) shows that increasing input tokens daramatically impacts llm performance.


## Notes:

### 1) Tool calls
- tools calls bloat context as its added to messages list, with call itself + tool results
- hence flush or summarise tools to reduce context length and keep context dense with just imoprtant info
- furthermore tools are suually injected at sytem prompt level which bloats context as well and leads to confusion of wghich tool to use.


### Context Offloading
...


### Context Compaction & Offloading




