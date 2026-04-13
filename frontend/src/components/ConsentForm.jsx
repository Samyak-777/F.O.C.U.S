/**
 * ConsentForm — Multilingual consent form component.
 * US-06: Explicit opt-in, non-pre-checked, 4 languages (en, hi, mr, te).
 * Props: { language: string, onConsent: function }
 */
import { useState } from 'react';

const CONSENT_TEXT = {
  en: {
    title: 'Biometric Data Consent',
    body: 'I understand that my facial features will be processed for attendance and engagement tracking. My data will be stored as encrypted embeddings only — no raw images are retained. I can withdraw consent at any time.',
    checkboxLabel: 'I give my consent for biometric data processing',
    submitLabel: 'Give Consent'
  },
  hi: {
    title: 'बायोमेट्रिक डेटा सहमति',
    body: 'मैं समझता/समझती हूँ कि मेरी चेहरे की विशेषताओं को उपस्थिति और सहभागिता ट्रैकिंग के लिए संसाधित किया जाएगा। मेरा डेटा केवल एन्क्रिप्टेड एम्बेडिंग के रूप में संग्रहीत किया जाएगा। मैं किसी भी समय सहमति वापस ले सकता/सकती हूँ।',
    checkboxLabel: 'मैं बायोमेट्रिक डेटा प्रसंस्करण के लिए अपनी सहमति देता/देती हूँ',
    submitLabel: 'सहमति दें'
  },
  mr: {
    title: 'बायोमेट्रिक डेटा संमती',
    body: 'मला समजते की माझ्या चेहऱ्याची वैशिष्ट्ये उपस्थिती आणि सहभाग ट्रॅकिंगसाठी प्रक्रिया केली जातील. माझा डेटा फक्त एन्क्रिप्टेड एम्बेडिंग म्हणून संग्रहित केला जाईल. मी कधीही संमती मागे घेऊ शकतो/शकते.',
    checkboxLabel: 'मी बायोमेट्रिक डेटा प्रक्रियेसाठी माझी संमती देतो/देते',
    submitLabel: 'संमती द्या'
  },
  te: {
    title: 'బయోమెట్రిక్ డేటా అంగీకారం',
    body: 'నా ముఖ లక్షణాలు హాజరు మరియు నిశ్చితార్థ ట్రాకింగ్ కోసం ప్రాసెస్ చేయబడతాయని నాకు అర్థమైంది. నా డేటా ఎన్‌క్రిప్టెడ్ ఎంబెడ్డింగ్‌లుగా మాత్రమే నిల్వ చేయబడుతుంది. నేను ఎప్పుడైనా అంగీకారాన్ని ఉపసంహరించుకోగలను.',
    checkboxLabel: 'బయోమెట్రిక్ డేటా ప్రాసెసింగ్ కోసం నా అంగీకారాన్ని ఇస్తున్నాను',
    submitLabel: 'అంగీకారం ఇవ్వండి'
  }
};

export default function ConsentForm({ language = 'en', onConsent }) {
  const [checked, setChecked] = useState(false);
  const text = CONSENT_TEXT[language] || CONSENT_TEXT.en;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (checked && onConsent) {
      onConsent({ language, timestamp: new Date().toISOString() });
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: '520px', padding: '24px' }}>
      <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '16px' }}>{text.title}</h2>
      <p style={{ fontSize: '14px', lineHeight: 1.6, marginBottom: '20px', color: '#cbd5e1' }}>
        {text.body}
      </p>

      <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', cursor: 'pointer', marginBottom: '20px' }}>
        <input
          type="checkbox"
          checked={checked}
          onChange={e => setChecked(e.target.checked)}
          aria-label="I give my consent for biometric data processing"
          style={{ marginTop: '3px' }}
        />
        <span style={{ fontSize: '14px' }}>{text.checkboxLabel}</span>
      </label>

      <button
        type="submit"
        disabled={!checked}
        aria-label="Give Consent"
        style={{
          padding: '10px 24px',
          fontSize: '14px',
          fontWeight: 600,
          borderRadius: '8px',
          border: 'none',
          cursor: checked ? 'pointer' : 'not-allowed',
          opacity: checked ? 1 : 0.5,
          backgroundColor: '#6366f1',
          color: '#fff'
        }}
      >
        {text.submitLabel}
      </button>
    </form>
  );
}
