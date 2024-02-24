# Haxxor Task Manager
## Ty Starry for stmp.gmail.com
![thanks](https://img.wattpad.com/76ac3646960f79f0953839da5ad50dcd3a22e197/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f776174747061642d6d656469612d736572766963652f53746f7279496d6167652f7343654b717242756675487049513d3d2d3534373535323236372e313531626465303062333734376533323436363234313936383636302e6a7067?s=fit&w=720&h=720)

# Overall description:
**A Haxxor Bunny (from Honkai Impact 3rd) themed Task Manager web application scripted with Python and its Flask framework, HTML (Jinja2 included), a little JavaScript, CSS and SQL.**

- Register/Log In
- Set Timezone (so that everything can be converted in UTC inside the SQL database)
- Add/Delete task
- Set user's email and verify it by an expiring (in 6h) token
- Set up to 5 reminders for each task
- Set reminders' email(s) on/off
- Send reminder during deadline as well

# INCOMPLETE
## remaining:
- **send email notifications to user during (already in UTC) datetimes inside users.db (more precisely reminders{1 <= i <= 5; i++} and deadline columns), AKA scheduled emailing**
