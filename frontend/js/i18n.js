// Internationalization (i18n) Support
const translations = {
    en: {
        'hero.title': 'Connect Workers with Job Providers',
        'hero.subtitle': 'Find skilled workers for your projects or discover job opportunities that match your skills',
        'features.title': 'Why Choose Job Workspace?',
        'features.workers.title': 'Skilled Workers',
        'features.workers.desc': 'Connect with verified and experienced workers',
        'features.ai.title': 'AI Matching',
        'features.ai.desc': 'Smart AI-powered matching for best job-worker fit',
        'features.secure.title': 'Secure Platform',
        'features.secure.desc': 'Safe and reliable job marketplace',
        'features.reviews.title': 'Reviews & Ratings',
        'features.reviews.desc': 'Transparent feedback system',
        'footer.desc': 'Connecting job providers with skilled workers',
        'footer.quick': 'Quick Links',
        'footer.contact': 'Contact'
    },
    si: {
        'hero.title': 'කම්කරුවන් රැකියා සපයන්නන් සමඟ සම්බන්ධ කරන්න',
        'hero.subtitle': 'ඔබේ ව්‍යාපෘති සඳහා කුසලතා සහිත කම්කරුවන් සොයා ගන්න හෝ ඔබේ කුසලතාවලට ගැලපෙන රැකියා අවස්ථා සොයා ගන්න',
        'features.title': 'Job Workspace තෝරන්නේ ඇයි?',
        'features.workers.title': 'කුසලතා සහිත කම්කරුවන්',
        'features.workers.desc': 'සත්‍යාපනය කරන ලද සහ අත්දැකීම් සහිත කම්කරුවන් සමඟ සම්බන්ධ වන්න',
        'features.ai.title': 'AI ගැලපීම',
        'features.ai.desc': 'හොඳම රැකියා-කම්කරු ගැලපීම සඳහා ස්මාර්ට් AI-බලගැන්වූ ගැලපීම',
        'features.secure.title': 'ආරක්ෂිත වේදිකාව',
        'features.secure.desc': 'ආරක්ෂිත සහ විශ්වාසදායක රැකියා වෙළඳපොළ',
        'features.reviews.title': 'සමාලෝචන සහ ශ්‍රේණිගත කිරීම්',
        'features.reviews.desc': 'විනිවිදභාවය සහිත ප්‍රතිපෝෂණ පද්ධතිය',
        'footer.desc': 'රැකියා සපයන්නන් කුසලතා සහිත කම්කරුවන් සමඟ සම්බන්ධ කිරීම',
        'footer.quick': 'ක්ෂණික සබැඳි',
        'footer.contact': 'සම්බන්ධ වන්න'
    },
    ta: {
        'hero.title': 'தொழிலாளர்களை வேலை வழங்குநர்களுடன் இணைக்கவும்',
        'hero.subtitle': 'உங்கள் திட்டங்களுக்கு திறமையான தொழிலாளர்களைக் கண்டறியவும் அல்லது உங்கள் திறன்களுடன் பொருந்தக்கூடிய வேலை வாய்ப்புகளைக் கண்டறியவும்',
        'features.title': 'Job Workspace ஏன் தேர்வு செய்ய வேண்டும்?',
        'features.workers.title': 'திறமையான தொழிலாளர்கள்',
        'features.workers.desc': 'சரிபார்க்கப்பட்ட மற்றும் அனுபவமுள்ள தொழிலாளர்களுடன் இணைக்கவும்',
        'features.ai.title': 'AI பொருத்தம்',
        'features.ai.desc': 'சிறந்த வேலை-தொழிலாளர் பொருத்தத்திற்கான ஸ்மார்ட் AI-இயக்கப்பட்ட பொருத்தம்',
        'features.secure.title': 'பாதுகாப்பான தளம்',
        'features.secure.desc': 'பாதுகாப்பான மற்றும் நம்பகமான வேலை சந்தை',
        'features.reviews.title': 'மதிப்புரைகள் மற்றும் மதிப்பீடுகள்',
        'features.reviews.desc': 'வெளிப்படையான கருத்து முறை',
        'footer.desc': 'வேலை வழங்குநர்களை திறமையான தொழிலாளர்களுடன் இணைத்தல்',
        'footer.quick': 'விரைவு இணைப்புகள்',
        'footer.contact': 'தொடர்பு'
    }
};

let currentLanguage = localStorage.getItem('language') || 'en';

function changeLanguage() {
    const select = document.getElementById('languageSelect');
    if (select) {
        currentLanguage = select.value;
        localStorage.setItem('language', currentLanguage);
        updatePageLanguage();
    }
}

function updatePageLanguage() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[currentLanguage] && translations[currentLanguage][key]) {
            element.textContent = translations[currentLanguage][key];
        }
    });
    
    // Update language selector
    const select = document.getElementById('languageSelect');
    if (select) {
        select.value = currentLanguage;
    }
}

// Initialize language on page load
document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('languageSelect');
    if (select) {
        select.value = currentLanguage;
    }
    updatePageLanguage();
});

