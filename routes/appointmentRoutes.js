import express from 'express';
import {
  getAllSpecializations,
  getHospitalsBySpecialization,
  getAllHospitals,
  getSpecializationsByHospital,
  getDoctorsByHospitalAndSpecialization,
  checkAvailableTimeSlots,
  bookAppointment,
  getPatientAppointments,
} from '../controllers/appointmentController.js';
import { authMiddleware } from '../middleware/authMiddleware.js';

const router = express.Router();

router.get('/specializations', getAllSpecializations);
router.get('/hospitals/specialization/:specialization', getHospitalsBySpecialization);
router.get('/hospitals', getAllHospitals);
router.get('/hospitals/:hospitalId/specializations', getSpecializationsByHospital);
router.get('/doctors', getDoctorsByHospitalAndSpecialization);
router.get('/timeslots', checkAvailableTimeSlots);

router.post('/:patientId/book', authMiddleware('patient'), bookAppointment);
router.get('/:patientId/appointments', authMiddleware('patient'), getPatientAppointments);

export default router;