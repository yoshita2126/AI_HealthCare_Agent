# Carepoint Access

A static patient, doctor, and staff login/register form.

Run MongoDB locally, then run `npm start` and open `http://localhost:3000`. The app uses `mongodb://localhost:27017/` and stores records in the `carepoint` database. Set `MONGODB_URI` to use another MongoDB connection. Accounts, follow-ups, prescriptions, chats, and emergency doctor assignments remain available after restarting the program. Opening `index.html` directly continues to use browser-local storage only.

Demo accounts:

- Patient: `patient@carepoint.demo` / `Patient123!`
- Doctor: `doctor@carepoint.demo` / `Doctor123!`
- Staff: `staff@carepoint.demo` / `Staff123!`

Select the matching role before signing in. New registrations are stored locally in the browser for this demo.
