import express from 'express';
import { registerPatient, loginPatient, getPatientProfile } from '../controllers/patientController.js';
import { authMiddleware } from '../middleware/authMiddleware.js';
import { getPatientAppointments } from '../controllers/appointmentController.js';
import { addHealthRecord, getHealthRecords, deleteHealthRecord } from '../controllers/healthRecordController.js'; // New controller
import multer from 'multer';
import path from 'path';

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname)); 
  },
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    const fileTypes = /pdf|jpeg|jpg|png/;
    const extname = fileTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = fileTypes.test(file.mimetype);
    if (extname && mimetype) {
      return cb(null, true);
    } else {
      cb(new Error('Only PDF and image files are allowed!'));
    }
  },
});

const router = express.Router();

router.post('/register', registerPatient);

router.post('/login', loginPatient);

router.get('/:patientId', authMiddleware('patient'), getPatientProfile);

router.get('/:patientId/appointments', authMiddleware('patient'), getPatientAppointments);

router.get('/:patientId/health-records', authMiddleware('patient'), getHealthRecords);
router.post('/:patientId/health-records', authMiddleware('patient'), upload.single('file'), addHealthRecord);
router.delete('/:patientId/health-records/:id', authMiddleware('patient'), deleteHealthRecord);

export default router;