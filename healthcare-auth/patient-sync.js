const patientQuery = new URLSearchParams(window.location.search);
const patientDisplayName = patientQuery.get('name');
const approvedBookings = JSON.parse(localStorage.getItem('carepointBookings') || '[]')
  .filter((booking) => booking.patient === patientDisplayName && booking.status === 'approved')
  .sort((first, second) => String(second.date || '').localeCompare(String(first.date || '')));
const approvedBooking = approvedBookings[0];

if (approvedBooking) {
  const doctorName = approvedBooking.doctorName || 'Assigned doctor';
  const appointmentDate = approvedBooking.date
    ? new Date(`${approvedBooking.date}T12:00:00`).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
    : 'Sep 08, 2026';
  document.querySelector('#appointment-type').textContent = approvedBooking.type || 'Consultation';
  document.querySelector('#appointment-date').textContent = appointmentDate;
  document.querySelector('#appointment-summary').textContent = `${appointmentDate} · ${approvedBooking.time || '02:00 PM'} · ${doctorName} · In person`;
  document.querySelector('#appointment-doctor').textContent = doctorName;
  document.querySelector('#booking-doctor').textContent = doctorName;
  document.querySelector('#patient-chat-doctor').textContent = doctorName;
  document.querySelector('#selected-doctor-name').textContent = doctorName;
  document.querySelectorAll('.record-doctor').forEach((element) => { element.textContent = doctorName; });
}
