# Fake Academy 🎓

Nowoczesny system zarządzania nauczaniem dla uczelni — platforma łącząca
oceny, komunikację, plan zajęć i materiały dydaktyczne w jednym miejscu.

Projekt edukacyjny realizowany w ramach przedmiotów: "Programowanie Front-end" (front-end) i "Nowatorski projekt indywidualny" (całość).

## O projekcie

Fake Academy to system klasy Librus/Vulcan, zaadaptowany do środowiska
akademickiego. Istniejące rozwiązania tego typu są zamknięte, kosztowne
i nie oferują tego, czego uczeń najbardziej potrzebuje: **information
feedback** — swobodnego, anonimowego głosu o jakości zajęć, oraz
narzędzi redukujących przeciążenie informacyjne wykładowców.

Fake Academy rozwiązuje trzy problemy:

- **Brak dwukierunkowego feedbacku** — studenci zgłaszają anonimowe
  opinie powiązane z konkretnym tematem zajęć, a wykładowcy otrzymują
  zanonimizowaną informację zwrotną o tym, co warto poprawić.
- **Przeciążenie informacyjne** — wbudowana sztuczna inteligencja
  generuje podsumowania ocen grupy, wątków wiadomości, opinii o zajęciach
  oraz treści materiałów tekstowych.
- **Rozproszenie informacji i koszt** — jedna platforma integrująca
  oceny, wiadomości, plan i materiały, zbudowana z otwartych
  technologii, w pełni skonteneryzowana i gotowa do wdrożenia
  w chmurze.

## Stack technologiczny

| Warstwa | Technologia |
| --- | --- |
| Frontend | React 18 + Vite, TypeScript, TanStack Query, Axios, Tailwind CSS |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic, PyJWT |
| Baza danych | PostgreSQL 16 |
| Magazyn plików | SeaweedFS (w 100% zgodne z API Amazon S3) |
| AI | Zewnętrzne API zgodne ze schematem OpenAI (podsumowania) |
| Konteneryzacja | Docker + Docker Compose |
| Serwowanie frontendu | Nginx (statyczny build Reacta) |

### Architektura

System ma postać dwóch aplikacji komunikujących się przez REST API
(HTTPS + JSON + uwierzytelnianie JWT):

- **Frontend (React)** — warstwa prezentacji; nie ma bezpośredniego
  dostępu do bazy ani magazynu plików.
- **Backend (FastAPI)** — cała logika biznesowa, autoryzacja (RBAC),
  walidacja danych; podzielony na moduły domenowe.
- **Usługi zewnętrzne** — PostgreSQL (dane), SeaweedFS (pliki, dostęp
  przez podpisane adresy URL), API AI (podsumowania tekstowe).

Całość uruchamiana jest jednym poleceniem `docker compose up` —
cztery kontenery: `frontend`, `backend`, `db`, `storage`.

## Zakres systemu

### Dla studenta
- wgląd we własne oceny (podział na przedmioty i kategorie, średnia ważona),
- plan zajęć własnej grupy,
- wiadomości do wykładowców i ogłoszenia grupowe,
- pobieranie materiałów dydaktycznych,
- anonimowe opinie o zajęciach (jedna opinia na temat zajęć),
- podsumowania AI materiałów tekstowych.

### Dla wykładowcy
- wystawianie ocen pojedynczo i masowo (cała grupa jednym formularzem),
  edycja ocen z audytem zmian,
- kategorie ocen z wagami (egzamin, kolokwium, projekt, aktywność),
- statystyki ocen grupy i eksport do CSV,
- prowadzenie korespondencji i ogłoszeń,
- udostępnianie materiałów,
- przeglądanie anonimowych opinii o własnych zajęciach — wyłącznie
  treść, temat i data, bez jakichkolwiek danych autora,
- podsumowania AI ocen, opinii i wiadomości.

### Dla administratora
- zarządzanie kontami i rolami (dezaktywacja zamiast usuwania),
- struktura uczelni: kierunki, grupy, przedmioty, przypisania,
- plan zajęć (sloty, sale),
- statystyki systemowe.

### Wspólne
- logowanie z tokenami JWT,
- powiadomienia in-app o ocenach, wiadomościach i zmianach planu.

## Anonimowość opinii

Opinia jest w bazie powiązana z autorem — wyłącznie po to, by zweryfikować,
czy student faktycznie uczęszcza na dane zajęcia, i ograniczyć spam
(jedna opinia na temat). Powiązanie to **nigdy nie jest zwracane
przez API** — wykładowca nie ma technicznej możliwości poznamy autora.

## Dokumentacja

Szczegółowy opis projektu (aktorzy, procesy biznesowe, funkcjonalności,
diagramy, schemat bazy danych, wdrożenie) znajduje się w dokumentacji
projektowej.

# Autorzy:
Kajetan 53497