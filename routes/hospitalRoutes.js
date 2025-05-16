import express from 'express';
import { registerHospital, loginHospital } from '../controllers/hospitalController.js';
import { getHospitalAppointments, updateAppointmentStatus } from '../controllers/appointmentController.js';
import { authMiddleware } from '../middleware/authMiddleware.js';

const router = express.Router();

router.post('/register', registerHospital);

router.post('/login', loginHospital);

router.get('/:hospitalId/pending-appointments', authMiddleware('hospital'), getHospitalAppointments);

router.put('/:hospitalId/appointments/:appointmentId/status', authMiddleware('hospital'), updateAppointmentStatus);

export default router;