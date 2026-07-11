# Sprint 3.19A - AI Provider Layer

Bu sprint iki çalışma modu ekler:

1. Lokal geliştirme:
   - AI_PROVIDER = "ollama"
   - Ollama localhost üzerinden çalışır.

2. Yayın / Streamlit Cloud:
   - AI_PROVIDER = "openai"
   - OPENAI_API_KEY Streamlit secrets içinden okunur.

Önemli:
- API anahtarını GitHub'a koyma.
- .streamlit/secrets.toml dosyasını commit etme.
- .streamlit/secrets.example.toml sadece örnek dosyadır.

Haber panelinde tek tek AI isteği atmak yerine toplu analiz kullanılır.
Amaç: 6 haber = 6 istek değil, 6 haber = 1 istek.
