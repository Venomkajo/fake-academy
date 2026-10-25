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
- wgląd we własne oceny (podział na przedmioty i kategorie, średnia
  ważona) i asystent AI odpowiadający na pytania o te oceny,
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

## Karty funkcji

Każda funkcja z sekcji [Zakres systemu](#zakres-systemu) ma poniżej własną
kartę według szablonu: **Co robi użytkownik / Widok / Dane / Najtrudniejsze /
Gotowe, gdy**. Właścicielem wszystkich funkcji jest autor projektu (projekt
solo).

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
- **Widok:** `/grades` — strona studenta (`GradesPage`); przedmioty jako
  rozwijane sekcje z kategoriami i średnią oraz panel „Zapytaj AI o oceny”
  (pole pytania → odpowiedź, historia pytań z bieżącej sesji).
- **Dane:** `GET /grades/me` → encje `grade`, `grade_category`, `subject`;
  średnia ważona liczona z wag kategorii. Pytania do AI idą przez
  `POST /ai/grades-qa` — backend przekazuje modelowi wyłącznie oceny
  pytającego studenta jako kontekst odpowiedzi.
- **Najtrudniejsze:** poprawność średniej ważonej przy kategoriach bez ocen
  i ocenach cząstkowych; grounding asystenta AI — odpowiedzi muszą
  wynikać wyłącznie z rzeczywistych ocen studenta; czytelne pogrupowanie dużej liczby wpisów.
- **Gotowe, gdy:** student widzi wszystkie oceny pogrupowane wg przedmiotu
  i kategorii, średnia zgadza się z obliczeniem ręcznym, a brak ocen
  pokazuje sensowny stan pusty; odpowiedź AI jest zgodna z widocznymi
  danymi (np. podana średnia = średnia na ekranie).
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### S2 · Plan zajęć własnej grupy

- **Co robi użytkownik:** Student przegląda tygodniowy plan zajęć swojej
  grupy (przedmiot, sala, godziny, wykładowca) i może zmieniać tydzień.
- **Widok:** `/schedule` — siatka tygodnia (`SchedulePage`), dni jako kolumny,
  sloty jako kafelki; nawigacja poprzedni/następny tydzień.
- **Dane:** `GET /schedule/me` → encje `lesson_slot`, `lesson_topic`,
  `subject`, `student_group`; widoczne wyłącznie sloty grup studenta.
- **Najtrudniejsze:** responsywny layout siatki i poprawne pozycjonowanie slotów w czasie.
- **Gotowe, gdy:** plan pokazuje wyłącznie zajęcia grup studenta, nawigacja
  tygodniami działa, a slot zawiera przedmiot, salę i godziny.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### S3 · Wiadomości do wykładowców i ogłoszenia grupowe

- **Co robi użytkownik:** Student wysyła wiadomości do wykładowców swoich
  przedmiotów, czyta wątki oraz ogłoszenia grupowe; widzi, które pozycje
  są nieprzeczytane.
- **Widok:** `/messages` — lista wątków + panel rozmowy; osobna zakładka
  ogłoszeń; licznik nieprzeczytanych w nawigacji.
- **Dane:** `GET/POST /messages` → encje `message`, `message_read_status`;
  odbiorcy ograniczeni do wykładowców studenta.
- **Najtrudniejsze:** utrzymanie spójnego stanu przeczytane/nieprzeczytane
  (synchronizacja licznika po wysłaniu/odczycie).
- **Gotowe, gdy:** student wyśle wiadomość do wykładowcy, zobaczy ją
  w wątku, ogłoszenia grupowe dotrą do wszystkich członków grupy,
  a licznik nieprzeczytanych jest aktualny.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### S4 · Pobieranie materiałów dydaktycznych

- **Co robi użytkownik:** Student przegląda materiały swoich przedmiotów
  (filtrowanie wg przedmiotu) i pobiera pliki jednym kliknięciem.
- **Widok:** `/materials` — lista plików z nazwą, przedmiotem, datą
  i przyciskiem pobrania.
- **Dane:** `GET /materials` → encja `material` (metadane) + podpisany URL
  pobierania z SeaweedFS wydawany przez backend.
- **Najtrudniejsze:** pobieranie przez podpisane adresy URL tak, by
  przeglądarka zapisała plik, i poprawna obsługa dużych plików.
- **Gotowe, gdy:** student filtruje listę wg przedmiotu, a pobrany plik
  otwiera się poprawnie lokalnie; niedostępny materiał pokazuje błąd.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### S5 · Anonimowe opinie o zajęciach (jedna na temat)

- **Co robi użytkownik:** Student wystawia anonimową opinię o konkretnym
  temacie zajęć; może sprawdzić, o które tematy już się wypowiedział,
  i nie może wystawić drugiej opinii do tego samego tematu.
- **Widok:** `/feedback` — lista tematów zajęć studenta z formularzem opinii
  i wyraźną informacją o anonimowości.
- **Dane:** `POST /feedback` → encje `feedback`, `lesson_topic`;
  unikalność (student, temat) pilnowana po stronie backendu.
- **Najtrudniejsze:** wiarygodna anonimowość — komunikacja UX (jasny
  komunikat, że wykładowca nie zobaczy autora) oraz obsługa próby
  powtórnej opinii bez ujawniania, kto próbował.
- **Gotowe, gdy:** student wystawia maksymalnie jedną opinię na temat,
  powtórna próba kończy się czytelnym komunikatem, a odpowiedź API
  nie zawiera żadnych danych autora.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### S6 · Podsumowania AI materiałów tekstowych

- **Co robi użytkownik:** Student klikając „Podsumuj" przy materiale
  tekstowym otrzymuje zwięzłe podsumowanie treści wygenerowane przez AI.
- **Widok:** `/materials` — przycisk „Podsumuj AI" przy materiale
  i panel z podsumowaniem (stan ładowania / wynik / błąd).
- **Dane:** treść materiału → backend → zewnętrzne API zgodne ze schematem
  OpenAI → zwrócone i cache'owane podsumowanie.
- **Najtrudniejsze:** UX długotrwałego zapytania (skeleton/spinner,
  timeout) i obsługa błędu przy niedostępności lub limicie API.
- **Gotowe, gdy:** podsumowanie pojawia się w rozsądnym czasie, wynik
  odnosi się do faktycznej treści materiału, a awaria API pokazuje
  zrozumiały błąd bez psucia strony.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

**Dla wykładowcy**

### W1 · Wystawianie ocen pojedynczo i masowo (z audytem zmian)

- **Co robi użytkownik:** Wykładowca wystawia ocenę pojedynczemu studentowi
  albo całej grupie jednym formularzem (wiersz na studenta), a także
  edytuje istniejące oceny, zapisywane do audytu.
- **Widok:** `/grades` (rola wykładowcy) — wybór przedmiotu/grupy, tryb
  pojedynczy i tryb masowy; historia zmian oceny w panelu szczegółów.
- **Dane:** `POST /grades`, `POST /grades/bulk`, `PATCH /grades/{id}` →
  encja `grade` + zapis audytu (kto, kiedy, stara → nowa wartość).
- **Najtrudniejsze:** formularz masowy — walidacja per wiersz, czytelne pokazanie historii
  zmian (audyt) na froncie.
- **Gotowe, gdy:** wykładowca wystawi oceny całej grupie jednym
  formularzem, edycja oceny zapisze wpis w audycie i historia jest
  jasno widoczna.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W2 · Kategorie ocen z wagami

- **Co robi użytkownik:** Wykładowca definiuje dla przedmiotu kategorie
  ocen (egzamin, kolokwium, projekt, aktywność) wraz z wagami wpływającymi
  na średnią ważoną studentów.
- **Widok:** `/grades/categories` — panel wykładowcy z listą kategorii
  i formularzem dodawania/edycji (nazwa + waga).
- **Dane:** `GET/POST/PATCH/DELETE /grade-categories` → encja
  `grade_category` (nazwa, waga, przypisanie do przedmiotu).
- **Najtrudniejsze:** implementacja średniej ważonej w backendzie i natychmiastowa aktualizacja
  średniej u studentów po zmianie wagi kategorii.
- **Gotowe, gdy:** wykładowca zarządza kategoriami przedmiotu, a zmiana
  wagi natychmiast wpływa na średnią ważoną widoczną u studenta.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W3 · Statystyki ocen grupy i eksport do CSV

- **Co robi użytkownik:** Wykładowca przegląda statystyki ocen grupy
  (średnia, rozkład ocen, wyniki per kategoria) i pobiera je jako plik CSV.
- **Widok:** `/statistics` — wybór przedmiotu/grupy, karty/podsumowania
  liczbowe, przycisk „Eksportuj CSV".
- **Dane:** agregacje z encji `grade`/`grade_category` (backend lub obliczenia
  po stronie frontendu); CSV generowane z polskimi znakami (UTF-8 BOM).
- **Najtrudniejsze:** poprawna agregacja w podziale na kategorie
  i uczciwa obsługa pustych zbiorów; CSV otwierany poprawnie w Excelu.
- **Gotowe, gdy:** statystyki zgadzają się z danymi na liście ocen,
  a pobrany CSV otwiera się w Excelu z poprawnymi polskimi znakami.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W4 · Korespondencja i ogłoszenia

- **Co robi użytkownik:** Wykładowca odpowiada na wiadomości studentów
  oraz publikuje ogłoszenia — do całej grupy lub wybranych studentów.
- **Widok:** `/messages` (rola wykładowcy) — lista wątków, panel rozmowy
  i kreator ogłoszenia z wyborem odbiorców.
- **Dane:** `GET/POST /messages` → encja `message` (typ: prywatna/ogłoszenie,
  nadawca, odbiorcy); wybór odbiorców ograniczony do grup wykładowcy.
- **Najtrudniejsze:** selektor odbiorców (tylko grupy przypisane
  wykładowcy — `teaching_assignment`) i spójność stanu przeczytania
  po obu stronach rozmowy.
- **Gotowe, gdy:** wykładowca odpowie na wiadomość studenta i opublikuje
  ogłoszenie grupowe, a studenci tej grupy zobaczą oba w swoich widokach.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W5 · Udostępnianie materiałów

- **Co robi użytkownik:** Wykładowca wgrywa pliki dla swoich przedmiotów,
  nadaje im opis i może je usuwać; studenci grupy widzą je od razu.
- **Widok:** `/materials` (rola wykładowcy) — formularz wgrywania
  (przedmiot, opis, plik) i lista własnych materiałów z akcjami.
- **Dane:** upload multipart → backend → SeaweedFS; metadane w encji
  `material` (przedmiot, autor, nazwa, rozmiar, data).
- **Najtrudniejsze:** pasek postępu i obsługa błędów przy dużych plikach
  oraz usuwanie (plik w SeaweedFS + wpis w bazie muszą zniknąć razem).
- **Gotowe, gdy:** wgrany plik jest widoczny i pobieralny dla studentów
  grupy, a jego usunięcie znika i z listy, i z magazynu.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W6 · Przeglądanie anonimowych opinii o własnych zajęciach

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
  w odpowiedzi API nie ma żadnych danych
  autora, a opinie dotyczą tylko jego zajęć.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

### W7 · Podsumowania AI ocen, opinii i wiadomości

- **Co robi użytkownik:** Wykładowca klika „Podsumuj AI" przy ocenach
  grupy, opiniach lub wątku wiadomości i otrzymuje zwięzłe podsumowanie
  redukujące przeciążenie informacyjne.
- **Widok:** `/statistics`, `/feedback`, `/messages` — przycisk „Podsumuj
  AI" i wspólny panel podsumowania (ładowanie / wynik / błąd).
- **Dane:** zagregowany tekst (oceny/feedback/wiadomości) → backend →
  zewnętrzne API zgodne ze schematem OpenAI → cache podsumowania.
- **Najtrudniejsze:** konstrukcja promptów dla trzech różnych typów
  danych, limity długości wejścia i kontrola kosztów/cache przy danych,
  które zmieniają się w czasie.
- **Gotowe, gdy:** podsumowanie każdego z trzech typów danych jest
  zgodne z treścią źródłową, generuje się z widocznym stanem ładowania,
  a błąd API nie blokuje pozostałych funkcji widoku.
- **Właściciel:** Kajetan Respondek (@Venomkajo)

**Dla administratora**

### A1 · Zarządzanie kontami i rolami

- **Co robi użytkownik:** Administrator przegląda listę kont, zmienia role
  (student/wykładowca/admin) i dezaktywuje konta zamiast je usuwać.
- **Widok:** `/admin/users` — tabela z filtrowaniem i wyszukiwaniem,
  formularz utworzenia konta, akcje zmiany roli/dezaktywacji.
- **Dane:** `GET/POST/PATCH /admin/users` → encja `user` (rola, `is_active`);
  dezaktywacja zamiast DELETE (ochrona powiązań w bazie).
- **Najtrudniejsze:** bezpieczeństwo — brak twardych usunięć (klucze
  obce w ocenach/wiadomościach), potwierdzenia przy zmianie roli
  i dezaktywacji własnego konta.
- **Gotowe, gdy:** administrator utworzy konto, zmieni rolę i dezaktywuje
  konto; zdezaktywowany użytkownik nie może się zalogować, a jego
  historyczne dane pozostają w systemie.
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

### C1 · Logowanie z tokenami JWT

- **Co robi użytkownik:** Użytkownik dowolnej roli loguje się e-mailem
  i hasłem, a system po weryfikacji przenosi go do widoku właściwego
  dla jego roli; sesja przeżywa odświeżenie strony.
- **Widok:** `/login`; chronione
  trasy w `App.tsx` — brak sesji odsyła do logowania.
- **Dane:** `POST /auth/login` → access token + refresh token (encje
  `refresh_token`); automatyczne odświeżenie access tokena i `POST /auth/logout`
  unieważniający sesję.
- **Najtrudniejsze:** poprawny cykl życia tokenów (odświeżanie bez
  nieskończonej pętli, logout czyszczący stan Axios/TanStack Query) oraz
  przeadresowanie po roli po zalogowaniu.
- **Gotowe, gdy:** logowanie działa dla wszystkich trzech ról z przekierowaniem
  do właściwego widoku, błędne dane pokazują komunikat, odświeżenie strony
  nie wylogowuje, a wylogowanie blokuje powrót przez wstecz/odnośnik.
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

# Autorzy:
Kajetan Respondek, 53497, @Venomkajo
