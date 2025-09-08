let currentSearchData = {};
let selectedHospital = {};

// Search form submission
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const location = document.getElementById('location').value;
            const serviceType = document.getElementById('serviceType').value;
            const urgency = document.getElementById('urgency').value;
            
            if (location.trim()) {
                currentSearchData = { location, serviceType, urgency };
                localStorage.setItem('searchData', JSON.stringify(currentSearchData));
                window.location.href = 'results.html';
            }
        });
    }
});
// Load hospitals for results page
async function loadHospitals() {
    try {
        const searchData = JSON.parse(localStorage.getItem('searchData') || '{}');
        document.getElementById('searchInfo').textContent = `Showing results for "${searchData.location}"`;

        // send location to backend API
        const response = await fetch(`/api/hospitals?location=${encodeURIComponent(searchData.location)}`);
        const hospitals = await response.json();

        const hospitalsList = document.getElementById('hospitalsList');
        hospitalsList.innerHTML = '';

        if (hospitals.length === 0) {
            hospitalsList.innerHTML = '<p>No hospitals found for this location.</p>';
            return;
        }

        hospitals.forEach(hospital => {
            const hospitalCard = createHospitalCard(hospital);
            hospitalsList.appendChild(hospitalCard);
        });
    } catch (error) {
        console.error('Error loading hospitals:', error);
        document.getElementById('hospitalsList').innerHTML = '<p>Error loading hospitals. Please try again.</p>';
    }
}


// Create hospital card HTML
function createHospitalCard(hospital) {
    const card = document.createElement('div');
    card.className = 'hospital-card';
    
    const crowdClass = hospital.crowd_level === 'Low' ? 'crowd-low' : 
                      hospital.crowd_level === 'Medium' ? 'crowd-medium' : 'crowd-high';
    
    card.innerHTML = `
        <div class="hospital-header">
            <div>
                <div class="hospital-name">${hospital.name}</div>
                <div class="hospital-address">📍 ${hospital.address}</div>
            </div>
            <div class="hospital-rating">${hospital.rating}★</div>
        </div>
        
        <div class="hospital-stats">
            <div class="stat-item">
                <div class="stat-label">Available Beds</div>
                <div class="stat-value">${hospital.available_beds}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Crowd Level</div>
                <div class="stat-value ${crowdClass}">${hospital.crowd_level}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Distance</div>
                <div class="stat-value">${hospital.distance}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Wait Time</div>
                <div class="stat-value">${hospital.wait_time}</div>
            </div>
        </div>
        
        <div class="hospital-actions">
            <button class="btn-book" onclick="bookAppointment('${hospital.id}')">
                📅 Book Appointment
            </button>
            <button class="btn-call" onclick="callHospital('${hospital.phone}')">
                📞 Call
            </button>
        </div>
    `;
    
    return card;
}

// Book appointment function
function bookAppointment(hospitalId) {
    localStorage.setItem('selectedHospitalId', hospitalId);
    window.location.href = 'booking.html';
}

// Call hospital function
function callHospital(phone) {
    window.location.href = `tel:${phone}`;
}

// Load hospital info for booking page
async function loadHospitalForBooking() {
    try {
        const hospitalId = localStorage.getItem('selectedHospitalId');
        const response = await fetch(`/api/hospital/${hospitalId}`);
        const hospital = await response.json();
        
        selectedHospital = hospital;
        
        const hospitalInfo = document.getElementById('hospitalInfo');
        hospitalInfo.innerHTML = `
            <h3>${hospital.name}</h3>
            <p>📍 ${hospital.address}</p>
            <p>📞 ${hospital.phone}</p>
            <p>⭐ Rating: ${hospital.rating}/5</p>
        `;
    } catch (error) {
        console.error('Error loading hospital:', error);
    }
}

// Set minimum date for appointment
function setMinDate() {
    const dateInput = document.getElementById('appointmentDate');
    if (dateInput) {
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        dateInput.min = tomorrow.toISOString().split('T')[0];
    }
}

// Booking form submission
document.addEventListener('DOMContentLoaded', function() {
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const bookingData = {
                hospital_id: localStorage.getItem('selectedHospitalId'),
                patient_name: document.getElementById('patientName').value,
                phone: document.getElementById('phone').value,
                email: document.getElementById('email').value,
                appointment_date: document.getElementById('appointmentDate').value,
                appointment_time: document.getElementById('appointmentTime').value,
                department: document.getElementById('department').value,
                symptoms: document.getElementById('symptoms').value
            };
            
            try {
                const response = await fetch('/api/booking', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(bookingData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    localStorage.setItem('bookingData', JSON.stringify(bookingData));
                    localStorage.setItem('bookingId', result.booking_id);
                    window.location.href = 'confirmation.html';
                } else {
                    alert('Booking failed. Please try again.');
                }
            } catch (error) {
                console.error('Error booking appointment:', error);
                alert('Booking failed. Please try again.');
            }
        });
    }
});

// Load booking confirmation
async function loadBookingConfirmation() {
    try {
        const bookingData = JSON.parse(localStorage.getItem('bookingData') || '{}');
        const bookingId = localStorage.getItem('bookingId');
        const hospitalId = localStorage.getItem('selectedHospitalId');
        
        const response = await fetch(`/api/hospital/${hospitalId}`);
        const hospital = await response.json();
        
        const bookingDetails = document.getElementById('bookingDetails');
        
        const appointmentDate = new Date(bookingData.appointment_date);
        const formattedDate = appointmentDate.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        bookingDetails.innerHTML = `
            <div style="text-align: center; background: rgba(33, 150, 243, 0.1); padding: 16px; border-radius: 8px; margin-bottom: 24px;">
                <p style="font-size: 14px; color: #666; margin-bottom: 4px;">Booking ID</p>
                <p style="font-size: 20px; font-weight: bold; color: #2196f3;">${bookingId}</p>
            </div>
            
            <h3 style="margin-bottom: 16px; color: #333;">Appointment Details</h3>
            
            <div class="detail-item">
                <span class="detail-icon">🏥</span>
                <div>
                    <div style="font-weight: 600;">${hospital.name}</div>
                    <div style="font-size: 14px; color: #666;">${hospital.address}</div>
                </div>
            </div>
            
            <div class="detail-item">
                <span class="detail-icon">📅</span>
                <div>
                    <div style="font-weight: 600;">${formattedDate}</div>
                </div>
            </div>
            
            <div class="detail-item">
                <span class="detail-icon">🕒</span>
                <div>
                    <div style="font-weight: 600;">${bookingData.appointment_time}</div>
                </div>
            </div>
            
            <div class="detail-item">
                <span class="detail-icon">👤</span>
                <div>
                    <div style="font-weight: 600;">${bookingData.patient_name}</div>
                    <div style="font-size: 14px; color: #666;">${bookingData.phone}</div>
                </div>
            </div>
            
            ${bookingData.department ? `
            <div class="detail-item">
                <span class="detail-icon">🏢</span>
                <div>
                    <div style="font-weight: 600;">${bookingData.department}</div>
                </div>
            </div>
            ` : ''}
            
            <div style="text-align: center; background: rgba(33, 150, 243, 0.1); padding: 12px; border-radius: 8px; margin-top: 16px;">
                <span style="color: #2196f3;">📞 Hospital: ${hospital.phone}</span>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading booking confirmation:', error);
    }
}

// Navigation functions
function goBack() {
    window.history.back();
}

function newSearch() {
    localStorage.clear();
    window.location.href = 'index.html';
}