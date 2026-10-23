# Fake Academy — frontend

React 18 + Vite + TypeScript. UI w **polsku**, kod i komentarze po angielsku.

## Uruchomienie

| Komenda (w `frontend/`) | Co robi |
| --- | --- |
| `npm run dev` | dev server Vite → http://localhost:5173 (HMR przy każdym zapisie) |
| `npm run build` | sprawdzenie typów (`tsc`) + produkcyjny bundle do `dist/` |
| `npm run preview` | podgląd zbudowanego bundle'a |

W Dockerze: `docker compose up frontend`. Kontener trzyma własne
`node_modules` w wolumenie nazwanym i przy każdym starcie uruchamia
`npm install` (`entrypoint.sh`), więc **po zmianie `package.json`
wystarczy zrestartować kontener** (`docker compose restart frontend`) —
nowe pakiety zainstalują się same. Pakiety można też dodać wprost
w kontenerze: `docker compose exec frontend npm install <pakiet>`
(aktualizuje `package.json` i `package-lock.json` na hoście przez mount).
`--build` jest potrzebny tylko po zmianie `Dockerfile` lub wersji Node.

## Struktura `src/`

```
src/
├── api/                  # wszystko, co rozmawia z backendem
│   ├── client.ts         # instancja axiosa + interceptor tokenu JWT
│   └── auth.ts           # login / me / tokeny, typy (UserPublic, Role)
├── components/
│   └── layout/           # szkielet aplikacji: Layout, Header, Navbar, Footer
├── pages/                # jeden komponent = jedna podstrona (route)
├── styles/
│   └── global.css        # design tokens (:root) + klasy UI
├── App.tsx               # bramka logowania + tablica tras (Routes)
└── main.tsx              # providerzy (QueryClient, BrowserRouter) + montaż
```

Providerzy w `main.tsx`:

- **React Router** (`react-router-dom`) — mapowanie URL ↔ komponent;
  `<Outlet/>` w `Layout` to miejsce, w którym renderuje się aktualna strona.
- **TanStack Query** (`@tanstack/react-query`) — pobieranie i cache'owanie
  danych z API; podpięty globalnie, jeszcze nieużywany — czeka na pierwszą
  „prawdziwą” stronę z danymi.

## Jak dodać nową stronę (3 kroki)

1. Utwórz `src/pages/MyPage.tsx`:

   ```tsx
   export default function MyPage() {
     return (
       <section className="card">
         <h1>Moja strona</h1>
       </section>
     )
   }
   ```

2. Zarejestruj trasę w `App.tsx` wewnątrz bloku
   `<Route element={<Layout …/>}>`:

   ```tsx
   <Route path="my-page" element={<MyPage />} />
   ```

3. Dodaj link w `Navbar.tsx` (tablica `LINKS` na górze pliku).

`Layout` pozostaje zamontowany podczas nawigacji — podmienia się tylko
`<Outlet/>`, więc header/navbar/footer nie „migają” i nie tracą stanu.

## Jak dodać nowy komponent

- Współdzielone cegiełki → `src/components/<domena>/MyComponent.tsx`
  (np. `components/grades/GradeTable.tsx`).
- Komponenty trzymaj **prezentacyjne**: dane wchodzą propsami, zdarzenia
  wychodzą callbackami (wzór: `Header` — `user` + `onLogout`).
- Jeden komponent domyślnie eksportowany na plik, nazwa pliku = nazwa komponentu.

## Kolejność pracy (sugestia)

1. **Header** — już podpięty do prawdziwych danych (user, wylogowanie);
   zostało doprawienie wyglądu (logo, layout).
2. **Navbar** — linki działają; następny krok: filtrowanie `LINKS`
   po `user.role` (student/wykładowca/admin widzą różne pozycje).
3. **Footer** — statyczny, kwestia wizualna.
4. **DashboardPage** — pierwszy prawdziwy ekran (np. ogłoszenia).
5. Dalej strony funkcjonalne (oceny, plan, wiadomości…) po kolei —
   każda to kopia schematu „3 kroki” powyżej.

## Konwencje i wskazówki

- Design tokens (kolory, promienie, cienie) to zmienne CSS w `:root`
  w `global.css` — zmieniaj tam, nie per komponent.
- Preferuj klasy CSS z `global.css` zamiast długich inline `style={{}}`
  (inline nie obsłuży `:hover` i nie skaluje się).
- Pobieranie danych: funkcje HTTP w `src/api/`, a w stronach
  `useQuery`/`useMutation` z TanStack Query — **nie** `useEffect` + `useState`.
- Gdy przekazywanie `user`/`onLogout` propsami zacznie przeszkadzać,
  wprowadź `AuthContext` + hook `useAuth()`.
- Opcjonalnie później: alias `@` → `src` (`resolve.alias` w `vite.config.ts`
  + `paths` w `tsconfig.json`), gdy relatywne importy się wydłużą.
