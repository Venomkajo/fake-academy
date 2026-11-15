# Fake Academy

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

## Szybki start (Windows)

Najprostsza droga do działającego środowiska to `start.bat` w katalogu
głównym repozytorium:

```bat
start.bat          :: build + start + migracje + seed (bezpieczne przy powtórce)
start.bat reset    :: pełny reset: kontenery, wolumeny, obrazy, cache — i świeży start
```

Skrypt sprawdza Dockera, w razie potrzeby tworzy `.env` oraz `frontend/.env`
z deweloperskimi wartościami domyślnymi, buduje obrazy, uruchamia wszystkie
kontenery, wykonuje migracje Alembic (`alembic upgrade head`) i zasilanie
bazy (`backend/scripts/seed.py`). Po zakończeniu wypisuje adresy usług
i konta testowe (`admin@fake.academy` / `admin123!` itd. — pełna lista
w `backend/scripts/seed.py`).

## Stack technologiczny

| Warstwa | Technologia |
| --- | --- |
| Frontend | React 18 + Vite, TypeScript, TanStack Query, Axios |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic, PyJWT |
| Baza danych | PostgreSQL 16 |
| Magazyn plików | SeaweedFS (w 100% zgodne z API Amazon S3) |
| AI | Zewnętrzne API zgodne ze schematem OpenAI (podsumowania) |
| Konteneryzacja | Docker + Docker Compose |

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
- wgląd we własne oceny (punkty 0–100, podział na przedmioty
  i kategorie, średnia ważona) i asystent AI odpowiadający na pytania
  o te oceny,
- plan zajęć własnej grupy,
- czat z wykładowcami swoich przedmiotów,
- pobieranie materiałów dydaktycznych,
- anonimowe opinie o zajęciach (jedna opinia na temat zajęć).

### Dla wykładowcy
- dziennik ocen: wystawianie i edycja ocen całej grupie w jednej tabeli
  (wiersz na studenta, kolumna na kategorię),
- kategorie ocen z wagami (egzamin, kolokwium, projekt, aktywność),
- statystyki ocen grupy i eksport do CSV,
- czat ze studentami swoich grup,
- ogłoszenia grupowe,
- udostępnianie materiałów (pliki do 20 MB),
- przeglądanie anonimowych opinii o własnych zajęciach — wyłącznie
  treść, temat i data,
- audyt zmian ocen (planowane: kto, kiedy, stara → nowa wartość).

### Dla administratora
- zarządzanie kontami i rolami (dezaktywacja zamiast usuwania),
- struktura uczelni: kierunki, grupy, przedmioty, przypisania,
- plan zajęć (sloty, sale),
- statystyki systemowe.

### Wspólne
- logowanie z tokenem JWT,
- pulpit startowy,
- przegląd grup (student: własne, wykładowca: prowadzone),
- powiadomienia in-app o ocenach, wiadomościach i zmianach planu,
- panel podsumowań AI (materiały, oceny, opinie, wiadomości).

## Karty funkcji

Każda funkcja z sekcji [Zakres systemu](#zakres-systemu) ma poniżej własną
kartę według szablonu: **Co robi użytkownik / Widok / Dane / Najtrudniejsze /
Gotowe, gdy** — z dodatkowymi polami (skala, mobile, limity, blokady) tam,
gdzie uszczegóławiają kryteria. Właścicielem wszystkich funkcji jest autor
projektu (projekt solo).

Ścieżki w polu *Widok* odnoszą się do docelowych tras w `App.tsx`;
adresy URL są angielskie, a etykiety widoczne
w interfejsie pozostają polskie.

**Dla studenta**

### S1 · Wgląd we własne oceny i pytania do AI o oceny

- **Co robi użytkownik:** Student przegląda wszystkie swoje oceny
  pogrupowane wg przedmiotów i kategorii (egzamin, kolokwium, projekt,
  aktywność); przy każdym przedmiocie widzi średnią ważoną. Może też
  zapytać asystenta AI o własne oceny — np. o średnią z przedmiotu albo
  o to, jaki wynik z egzaminu zapewni mu ocenę docelową.
- **Skala:** oceny to punkty 0–100 (kategorie zaliczeniowe mają zamiast
  punktów symbol ZAL/NZAL). Średnia ważona to też punkty — np. „87.50”,
  bez jednostki; kategorie ZAL/NZAL nie wchodzą do średniej. System
  nie przelicza punktów na ocenę 2–5 — taka skala w nim nie istnieje.
- **Widok:** `/grades` — strona studenta (`GradesPage`); przedmioty jako
  rozwijane sekcje z kategoriami i średnią oraz panel „Zapytaj AI o oceny”
  (pole pytania → odpowiedź, historia pytań z bieżącej sesji).
- **Dane:** `GET /grades/me` → encje `grade`, `grade_category`, `subject`;
  średnia ważona liczona z wag kategorii. Pytania do AI idą przez
  `POST /ai/grades-qa` — backend przekazuje modelowi wyłącznie oceny
  pytającego studenta jako kontekst odpowiedzi.
- **Najtrudniejsze:** poprawność średniej ważonej — Σ(ocena × waga) /
  Σ(waga) po kategoriach z punktami, więc kategorie bez ocen i same
  ZAL/NZAL nie zniekształcają wyniku; grounding asystenta AI (odpowiedzi
  wyłącznie z rzeczywistych ocen studenta); czytelne pogrupowanie dużej
  liczby wpisów.
- **Gotowe, gdy:** student widzi wszystkie oceny pogrupowane wg przedmiotu
  i kategorii, średnia zgadza się z obliczeniem ręcznym, brak ocen pokazuje
  sensowny stan pusty, a odpowiedź AI jest zgodna z widocznymi danymi.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### S2 · Plan zajęć własnej grupy

- **Co robi użytkownik:** Student przegląda tygodniowy plan zajęć swojej
  grupy (przedmiot, sala, godziny, wykładowca) i może zmieniać tydzień.
- **Widok:** `/schedule` — siatka tygodnia (`SchedulePage`), dni jako kolumny,
  sloty jako kafelki; nawigacja poprzedni/następny/bieżący tydzień.
- **Dane:** `GET /schedule/me` → encje `lesson_slot`, `subject`,
  `student_group` (przez `teaching_assignment`); widoczne wyłącznie sloty
  grup studenta. Sloty są cykliczne (bez dat), więc zmiana tygodnia
  przełącza tylko daty w nagłówkach kolumn.
- **Mobile:** do ok. 720 px pełna siatka pięciu kolumn; poniżej siatka
  zachowuje minimalną szerokość i przewija się w poziomie, a nagłówek
  zawija się w wiersze.
- **Pusty stan:** grupa bez zajęć pokazuje komunikat „Twoje grupy nie mają
  jeszcze żadnych zajęć w planie” zamiast pustej siatki.
- **Najtrudniejsze:** poprawne pozycjonowanie slotów w czasie (kafelki
  zajęć nakładających się w jednym dniu dzielą szerokość kolumny).
- **Gotowe, gdy:** plan pokazuje wyłącznie zajęcia grup studenta, nawigacja
  tygodniami działa, slot zawiera przedmiot, salę i godziny, na telefonie
  plan da się przewinąć w poziomie, a tydzień bez zajęć kończy się
  czytelnym komunikatem.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### S3 · Czat z wykładowcami

- **Co robi użytkownik:** Student wysyła wiadomości do wykładowców
  przedmiotów, które uczęszcza, i czyta wątki; widzi, które pozycje
  są nieprzeczytane.
- **Widok:** `/messages` — zakładka „Rozmowy”: lista wątków z licznikami
  nieprzeczytanych + panel rozmowy z formularzem odpowiedzi; licznik
  nieprzeczytanych w nawigacji.
- **Dane:** `GET/POST /messages`, `POST /messages/{id}/read` → encje
  `message`, `message_read_status`; odbiorcy ograniczeni do wykładowców
  przedmiotów studenta.
- **Najtrudniejsze:** spójność stanu przeczytane/nieprzeczytane —
  otwarcie wątku, wysłanie i odpowiedź unieważniają wspólną pamięć
  `['messages']` (TanStack Query), więc lista i licznik w nawigacji
  odświeżają się bez przeładowania strony.
- **Gotowe, gdy:** student wyśle wiadomość do wykładowcy i zobaczy ją
  w wątku, odpowiedź wykładowcy dojdzie do tego samego wątku, a licznik
  nieprzeczytanych zgadza się z listą wątków.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### S4 · Pobieranie materiałów dydaktycznych

- **Co robi użytkownik:** Student przegląda materiały swoich przedmiotów
  (filtrowanie wg przedmiotu) i pobiera pliki jednym kliknięciem.
- **Widok:** `/materials` — lista plików z nazwą, przedmiotem, datą
  i przyciskiem pobrania.
- **Dane:** `GET /materials` → encja `material` (metadane) + podpisany URL
  pobierania z SeaweedFS wydawany przez backend.
- **Limity:** limit wielkości plików 20 MB — próba wgrania większego kończy się komunikatem
  o limicie
- **Najtrudniejsze:** pobieranie przez podpisany adres URL tak, by
  przeglądarka zapisała plik, oraz czytelny błąd, gdy materiał
  jest niedostępny (np. plik usunięty w magazynie).
- **Gotowe, gdy:** student filtruje listę wg przedmiotu, pobrany plik
  otwiera się poprawnie lokalnie, a niedostępny materiał pokazuje
  komunikat błędu.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### S5 · Anonimowe opinie o zajęciach (jedna na temat)

- **Co robi użytkownik:** Student wystawia anonimową opinię o konkretnym
  temacie zajęć; nie może wystawić drugiej opinii do tego samego tematu.
- **Widok:** `/feedback` — lista tematów zajęć studenta z formularzem
  opinii i wyraźną informacją o anonimowości; przy każdym temacie widać,
  czy student już się wypowiedział.
- **Dane:** `POST /feedback` → encje `feedback`, `lesson_topic`;
  unikalność (student, temat) pilnowana po stronie backendu.
- **Najtrudniejsze:** wiarygodna anonimowość — jasny komunikat, że
  wykładowca nie zobaczy autora, oraz obsługa próby powtórnej opinii
  bez ujawniania, kto próbował.
- **Gotowe, gdy:** student widzi na liście stan „opinia już wystawiona”,
  powtórna próba kończy się czytelnym komunikatem, a odpowiedź API
  nie zawiera żadnych danych autora.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

**Dla wykładowcy**

### W1 · Dziennik ocen — wystawianie i edycja w jednym miejscu

- **Co robi użytkownik:** Wykładowca wybiera przypisanie (przedmiot ×
  grupa) i wystawia lub edytuje oceny w dzienniku: wiersz na studenta,
  kolumna na kategorię; wpisanie wartości i Enter zapisuje komórkę
  (POST przy pustej, PATCH przy istniejącej).
- **Widok:** `/grades` (rola wykładowcy) — wybór przypisania jako przyciski,
  panel kategorii i tabela dziennika z edytowalnymi komórkami.
- **Dane:** `GET /grades/teaching`, `GET /grades/assignment/{id}/sheet`,
  `POST /grades`, `PATCH /grades/{id}` → encje `grade`, `grade_category`.
- **Najtrudniejsze:** walidacja komórki (liczba 0–100 z „,” lub „.”
  jako separatorem albo ZAL/NZAL) i zapis bez przeładowania;
  konflikt (ocena już istnieje) pokazuje błąd pod komórką.
- **Gotowe, gdy:** wykładowca wystawi oceny wszystkim studentom grupy
  w jednej tabeli, edycja istniejącej oceny zapisuje się od razu,
  a niepoprawna wartość pokazuje błąd pod komórką.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W2 · Kategorie ocen z wagami

- **Co robi użytkownik:** Wykładowca definiuje dla przypisania kategorie
  ocen (egzamin, kolokwium, projekt, aktywność) wraz z wagami wpływającymi
  na średnią ważoną studentów; kategorie bez ocen może usuwać.
- **Widok:** panel kategorii w `/grades` (rola wykładowcy) — lista kategorii
  wybranego przypisania i formularz dodawania (nazwa + waga).
- **Dane:** kategorie w odpowiedzi `GET /grades/teaching`,
  `POST /grades/categories`, `DELETE /grades/categories/{id}` → encja
  `grade_category` (nazwa, waga, przypisanie).
- **Reguła wag:** waga to procentowy udział kategorii w średniej ważonej;
  suma wag nie musi wynosić 100 (średnia dzieli przez sumę wag kategorii
  z ocenami), ale 100% jest wartością zalecaną.
- **Najtrudniejsze:** spójność — kategoria z ocenami jest nietykalna
  (usuwanie zwraca 409), a średnie studentów liczą się z aktualnych wag.
- **Gotowe, gdy:** wykładowca dodaje kategorię z wagą i od razu widzi ją
  w dzienniku, próba usunięcia kategorii z ocenami kończy się blokadą,
  a zmiana wagi zmienia średnie studentów.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W3 · Statystyki ocen grupy i eksport do CSV

- **Co robi użytkownik:** Wykładowca przegląda statystyki ocen grupy
  (średnia, rozkład ocen, wyniki per kategoria) i pobiera je jako plik CSV.
- **Widok:** `/statistics` — wybór przedmiotu/grupy, karty/podsumowania
  liczbowe, przycisk „Eksportuj CSV".
- **Dane:** agregacje liczone na froncie z istniejącego arkusza
  `GET /grades/assignment/{id}/sheet` (encje `grade`/`grade_category`);
  CSV generowane z polskimi znakami (UTF-8 BOM).
- **Najtrudniejsze:** poprawna agregacja w podziale na kategorie
  i uczciwa obsługa pustych zbiorów (komunikat zamiast zer);
  CSV otwierane poprawnie w Excelu.
- **Gotowe, gdy:** statystyki zgadzają się z danymi na liście ocen,
  a pobrany CSV otwiera się w Excelu z poprawnymi polskimi znakami.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W4 · Czat ze studentami
 
- **Co robi użytkownik:** Wykładowca czyta wątki ze studentami swoich grup
  i odpowiada na ich wiadomości.
- **Widok:** `/messages` (rola wykładowcy) — zakładka „Rozmowy”: lista wątków
  + panel rozmowy z odpowiedzią; licznik nieprzeczytanych w nawigacji.
- **Dane:** `GET/POST /messages`, `POST /messages/{id}/read` → encje
  `message`, `message_read_status`; kontakty ograniczone do studentów
  grup wykładowcy (`teaching_assignment`).
- **Najtrudniejsze:** spójność stanu przeczytania po obu stronach rozmowy
  (wspólna pamięć `['messages']` jak w S3).
- **Gotowe, gdy:** wykładowca odpowie na wiadomość studenta, student
  zobaczy odpowiedź w tym samym wątku, a liczniki nieprzeczytanych
  zgadzają się po obu stronach.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W5 · Ogłoszenia grupowe

- **Co robi użytkownik:** Wykładowca publikuje ogłoszenie do wybranej
  grupy — z tytułem i treścią; ogłoszenie trafia do wszystkich studentów
  grupy, a otwarcie oznacza je jako przeczytane.
- **Widok:** `/messages` (rola wykładowcy) — zakładka „Ogłoszenia”
  z kreatorem (grupa, tytuł, treść) i listą opublikowanych; studenci
  widzą je w tej samej zakładce u siebie.
- **Dane:** `GET/POST /messages` → encja `message` (typ: ogłoszenie,
  nadawca, grupa); wybór grupy ograniczony do grup wykładowcy
  (`teaching_assignment`).
- **Najtrudniejsze:** skierowanie ogłoszenia tylko do właściwej grupy
  (backend weryfikuje grupę) i spójność liczników nieprzeczytanych
  u wszystkich odbiorców.
- **Gotowe, gdy:** wykładowca opublikuje ogłoszenie grupowe, każdy student
  grupy je zobaczy, a otwarcie ogłoszenia zdejmie je z licznika
  nieprzeczytanych.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W6 · Udostępnianie materiałów

- **Co robi użytkownik:** Wykładowca wgrywa pliki dla przedmiotów
  swoich przypisań i może je usuwać; studenci grupy widzą je od razu.
- **Widok:** `/materials` (rola wykładowcy) — formularz wgrywania
  (przedmiot, plik) i lista własnych materiałów z akcjami.
- **Dane:** upload multipart → backend → SeaweedFS; metadane w encji
  `material` (przedmiot, autor, nazwa, rozmiar, data).
- **Limity:** plik do 20 MB — próba wgrania większego kończy się
  komunikatem o limicie (walidowane przed wysłaniem i na backendzie).
- **Najtrudniejsze:** usuwanie (plik w SeaweedFS + wpis w bazie muszą
  zniknąć razem) i obsługa błędu uploadu bez utraty formularza.
- **Gotowe, gdy:** wgrany plik jest widoczny i pobieralny dla studentów
  grupy, plik ponad 20 MB kończy się komunikatem o limicie, a usunięcie
  znika i z listy, i z magazynu.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W7 · Przeglądanie anonimowych opinii o własnych zajęciach

- **Co robi użytkownik:** Wykładowca przegląda opinie studentów o swoich
  zajęciach — wyłącznie treść, temat i datę; nie widzi i nie może ustalić
  autora opinii.
- **Widok:** `/feedback` (rola wykładowcy) — lista opinii pogrupowana wg
  przedmiotu/tematu, bez jakichkolwiek kolumn autora.
- **Dane:** `GET /feedback` — odpowiedź zawiera wyłącznie treść, temat
  i datę; filtrowanie po przedmiotach prowadzonych przez wykładowcę.
- **Najtrudniejsze:** zapewnienie braku przecieku — schema odpowiedzi
  nie może zawierać pól autora ani identyfikatorów pozwalających
  wnioskować o osobie; UI nie może sugerować autorstwa.
- **Gotowe, gdy:** wykładowca widzi wyłącznie treść, temat i datę;
  w odpowiedzi API nie ma żadnych danych autora, a opinie dotyczą
  tylko jego zajęć.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W8 · Audyt zmian ocen

- **Co robi użytkownik:** Wykładowca przegląda historię zmian oceny —
  kto, kiedy, jaka wartość poprzednia i nowa.
- **Widok:** panel szczegółów oceny w `/grades` (rola wykładowcy).
- **Dane:** encja `grade_audit` (planowana migracja) zapisywana przy
  `POST /grades` i `PATCH /grades/{id}`.
- **Najtrudniejsze:** odróżnienie wystawienia od edycji w historii
  i czytelne pokazanie „stara → nowa wartość" na froncie.
- **Gotowe, gdy:** edycja oceny zapisuje wpis w audycie, a historia zmian
  jest jasno widoczna w panelu oceny.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W9 · Panel podsumowań AI

- **Co robi użytkownik:** Student klika „Podsumuj AI" przy materiale
  tekstowym; wykładowca — przy ocenach grupy, opiniach o zajęciach
  i wątku wiadomości. Otrzymuje zwięzłe podsumowanie redukujące
  przeciążenie informacyjne.
- **Widok:** wspólny panel podsumowania przy `/materials`,
  `/statistics`, `/feedback`, `/messages` — przycisk wywołuje,
  panel pokazuje ładowanie / wynik / błąd (wspólny komponent
  we wszystkich widokach).
- **Dane:** treść (materiał / oceny / opinie / wiadomości) → backend →
  zewnętrzne API zgodne ze schematem OpenAI (`AI_API_BASE_URL`,
  `AI_MODEL`) → zwrócone i cache'owane podsumowanie; pytania o oceny
  studenta przez `POST /ai/grades-qa` (S1).
- **Najtrudniejsze:** konstrukcja promptów dla różnych typów danych,
  limity długości wejścia i kontrola kosztów/cache przy danych,
  które zmieniają się w czasie.
- **Gotowe, gdy:** podsumowanie każdego typu danych jest zgodne
  z treścią źródłową, generuje się z widocznym stanem ładowania,
  a błąd API jest czytelnie komunikowany.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

**Dla administratora**

### A1 · Zarządzanie kontami i rolami

- **Co robi użytkownik:** Administrator przegląda listę kont
  z wyszukiwaniem (fragment imienia, nazwiska lub e-maila) i filtrem
  roli, edytuje dane (imię, nazwisko, e-mail), zmienia role
  (student/wykładowca/admin) i dezaktywuje konta zamiast je usuwać.
- **Widok:** `/admin/users` — tabela z inline edycją (Edytuj ładuje
  wiersz do formularza) + wyszukiwarka i filtr roli nad tabelą.
- **Dane:** `GET/PATCH /admin/users` → encja `user` (rola, `is_active`);
  dezaktywacja zamiast DELETE (ochrona powiązań w bazie).
- **Blokady:** administrator nie może zmienić własnej roli ani
  dezaktywować własnego konta.
- **Najtrudniejsze:** bezpieczeństwo — brak twardych usunięć (klucze
  obce w ocenach/wiadomościach) i blokada samozmiany roli
  i samodezaktywacji.
- **Gotowe, gdy:** administrator zmieni rolę i dezaktywuje konto,
  zdezaktywowany użytkownik nie może się zalogować (403), jego dane
  historyczne zostają w systemie, a próba zmiany własnej roli lub
  dezaktywacji własnego konta kończy się odmową.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### A2 · Struktura uczelni (kierunki, grupy, przedmioty, przypisania)

- **Co robi użytkownik:** Administrator buduje strukturę uczelni: tworzy
  kierunki, grupy studenckie, przedmioty oraz przypisania — wykładowców
  do przedmiotów (z grupami) i studentów do grup.
- **Widok:** `/admin/structure` — panel z zakładkami/kartami per encja
  i formularze przypisań (osoba ↔ grupa ↔ przedmiot).
- **Dane:** `GET/POST/PATCH /admin/...` → encje `field_of_study`,
  `student_group`, `subject`, `teaching_assignment`, `group_membership`.
- **Najtrudniejsze:** formularze encji od siebie zależnych (kolejność:
  kierunek → grupa → przedmiot → przypisanie) i walidacja spójności
  (student tylko w jednej grupie na kierunek, wykładowca per przedmiot).
- **Gotowe, gdy:** administrator przejdzie pełną ścieżkę: kierunek →
  grupa → przedmiot → przypisania, a utworzona struktura jest widoczna
  w widokach studenta i wykładowcy (oceny, plan, materiały).
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### A3 · Plan zajęć (sloty, sale)

- **Co robi użytkownik:** Administrator układa plan zajęć: dodaje sloty
  (przedmiot, grupa, wykładowca, sala, dzień i godzina) oraz tematy zajęć,
  do których studenci mogą wystawiać opinie.
- **Widok:** `/admin/schedule` — edytor slotów na siatce tygodnia (podobnej
  do widoku studenckiego, ale z akcjami dodaj/edytuj/usuń) + zarządzanie
  tematami zajęć.
- **Dane:** `GET/POST/PATCH/DELETE /admin/lesson-slots` → encje
  `lesson_slot` (sala, czas, grupa, przedmiot), `lesson_topic`.
- **Najtrudniejsze:** walidacja kolizji — jedna sala, jedna grupa
  i jeden wykładowca nie mogą mieć dwóch zajęć w tym samym czasie;
  czytelne komunikaty konfliktów.
- **Gotowe, gdy:** administrator doda slot, próba nałożenia slotów
  w tej samej sali/grupie/wykładowcy w jednym czasie zostanie odrzucona
  z jasnym błędem, a slot pojawi się w planach studentów i wykładowców.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### A4 · Statystyki systemowe

- **Co robi użytkownik:** Administrator podgląda kluczowe metryki systemu
  (liczba użytkowników per rola, ocen, wiadomości, opinii, materiałów),
  żeby ocenić użycie platformy.
- **Widok:** `/admin/statistics` — pulpit z kartami liczników
  i prostymi wykresami.
- **Dane:** `GET /admin/stats` — agregacje licznikowe z tabel `user`,
  `grade`, `message`, `feedback`, `material`.
- **Najtrudniejsze:** wydajne agregacje i sensowna wizualizacja bez nadmiarowego narzędzia.
- **Gotowe, gdy:** pulpit pokazuje poprawne liczniki zgodne ze stanem
  bazy i odświeża się na żądanie.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

**Wspólne (wszyscy)**

### C1 · Logowanie z tokenem JWT

- **Co robi użytkownik:** Użytkownik dowolnej roli loguje się e-mailem
  i hasłem; po weryfikacji trafia na pulpit (`/`), a sesja przeżywa
  odświeżenie strony.
- **Widok:** `/login` — formularz e-mail + hasło; wszystkie trasy
  w `App.tsx` są chronione: brak sesji pokazuje login zamiast strony.
- **Dane:** `POST /auth/login` → access token (JWT, domyślnie 60 min)
  przechowywany w localStorage; `GET /auth/me` sprawdza token po starcie
  aplikacji; wygasły token (401) jest usuwany przez interceptor Axiosa,
  który przeładowuje aplikację do loginu.
- **Najtrudniejsze:** cykl życia tokena bez nieskończonej pętli
  (interceptor reaguje tylko na 401 z wysłanym tokenem) oraz jeden
  wspólny komunikat i czas odpowiedzi dla złego e-maila i hasła.
- **Gotowe, gdy:** logowanie działa dla wszystkich trzech ról, błędne
  dane pokazują komunikat, odświeżenie strony nie wylogowuje,
  a po wylogowaniu powrót wstecz pokazuje login.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### C2 · Powiadomienia in-app

- **Co robi użytkownik:** Użytkownik widzi powiadomienia (ikona dzwonka
  z licznikiem) o nowych ocenach, wiadomościach i zmianach planu; może
  oznaczyć je jako przeczytane.
- **Widok:** dzwonek w `Header`/`Navbar` + rozwijana lista powiadomień;
  kliknięcie prowadzi do właściwej strony.
- **Dane:** `GET /notifications`, `PATCH /notifications/{id}/read` →
  encja `notification` (typ, treść, link docelowy, przeczytane);
  tworzona przez backend przy ocenie, wiadomości, zmianie planu.
- **Najtrudniejsze:** odczuwalna „natychmiastowość" bez web-socketów —
  odpytywanie/aktualizacja licznika i niegubienie 
  powiadomień przy wielu otwartych kartach.
- **Gotowe, gdy:** wystawienie oceny, nowa wiadomość i zmiana planu
  generują powiadomienie widoczne bez przeładowania strony, licznik
  nieprzeczytanych jest zgodny na wszystkich widokach, a oznaczenie
  przeczytanym trwale je ukrywa z licznika.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### C3 · Pulpit startowy

- **Co robi użytkownik:** Po zalogowaniu użytkownik dowolnej roli widzi
  pulpit z powitaniem — pierwszy ekran aplikacji.
- **Widok:** `/` (`DashboardPage`) — powitanie, e-mail i rola
  zalogowanego użytkownika; placeholder docelowego pulpitu
  (ogłoszenia, ostatnie oceny, najbliższe zajęcia).
- **Dane:** `GET /auth/me` → encja `user`; bez własnych zapytań.
- **Najtrudniejsze:** docelowo zróżnicowanie treści wg roli bez
  pisania tego samego layoutu trzykrotnie.
- **Gotowe, gdy:** każdy zalogowany użytkownik po wejściu na `/`
  widzi swoje dane i może przejść do dalszych sekcji z nawigacji.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### C4 · Przegląd grup

- **Co robi użytkownik:** Student widzi grupy, do których należy (nazwa,
  kierunek, liczba członków); wykładowca — grupy, które prowadzi,
  po jednym wierszu na przypisanie (przedmiot × grupa × kierunek).
- **Widok:** `/groups` (`GroupsPage`) — tabela `data-table`;
  administrator widzi notkę odsyłającą do „Struktury uczelni”.
- **Dane:** `GET /groups/me` (student), `GET /groups/teaching`
  (wykładowca) → encje `student_group`, `field_of_study`,
  `teaching_assignment`.
- **Najtrudniejsze:** uruchomienie tylko właściwego zapytania dla roli
  (TanStack `enabled`), by wykładowca nie wywołał końcówki studenta.
- **Gotowe, gdy:** student widzi swoje grupy z liczbą członków,
  wykładowca swoje przypisania, a pusta lista pokazuje komunikat
  o braku grup.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

# Autorzy:
Kajetan Respondek, 53497, @Venomkajo
