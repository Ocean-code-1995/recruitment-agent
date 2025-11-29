## ***`Example Queries`***
---

### ***`Tool Availabiity`***

Use the following prompt to see if it cann see the tools atatched to the agent without having to mention in systemn prompt, since when passing the tools as list in `create_agent`it alkready takes care of that.
```text
hey what tools do you have avialable? please give comprehensive info and overview
```
**NOTE** 
In my last run it listed an additional tool called `Multi-Tool Use (multi_tool_use.parallel)`. This is NOT a real tool in the codebase but an internal OpenAI artifact representing the model's capability to call multiple tools in parallel. It can be ignored.

### ***`Already working:`***
```text
>>> Hey is there any candidates in our databse?

>>> Great tell me more about this person!

>>> Ok so please send him an email and notify him that his cv has been screened!

>>> Please udate his status from cv screened to applied!

>>> I checked his cv and it looks great by manual inspection by myself. hence can we set his interview status to scheduled?
```


### ***`Goals:`***
```text
>>> Since his cv was screened, can you update his interview status as completed and decision status as maybe?

>>> Since his cv was screened, can you update his interview status as completed and decision status as maybe? Then also send him an email that we will soon schedule a person-to-person interview with him.

>>> can you send him an email that we liked his cv and want to schedule a meeting with him for for the foloowing friday at 3pm? After sending the email please update interview scheduling statius as 'scheduled'

---

>>> Please schedule an interview for that person for this friday 2pm and then notfiy the applicant that he has an personal interview at that time and shall mark it in his calendar.

>>> Please schedule an interview in our hr calendar that candidate x will have an person-to-person interview. Also notofy both hr and the applicant by email and send ***calendar invitation** to the candidate!


>>> Please check in our HR calendar what days havee available slots for an 1h interview. Once we found we found that out we suggest the candidate the available time slots. Once he agrees to one slot we can schedule that agreed slot. 

>>> Can you please send an calendar invite to that person for this friday 2pm and to HR as well?

>>>
```
