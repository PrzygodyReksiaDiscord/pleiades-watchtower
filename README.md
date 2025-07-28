# Strażnica Plejad

W niniejszym repozytorium przechowywane są pliki konfiguracyjne kanału #plejada-gwiazd serwera Przygody Reksia Discord. Kanał złożony jest z wątków (dalej: albumów) przypisanych konkretnym użytkownikom.
W albumach znajdują się tekstowo-obrazkowe embedy (dalej: naklejki) przyznawane użytkownikom za szczególne osiągnięcia związane ogólnie ze społecznością fanów Reksia.

## Struktura konfiguracji

- lista naklejek zdefiniowana jest w pliku [stickers.json5](./stickers.json5)
- lista kategorii oraz przyporządkowanie do nich naklejek określone są w pliku [categories.json5](./categories.json5)
- grafiki naklejek można wrzucać gdziekolwiek, ale najlepiej je jakoś ładnie poukładać w foldery
- przyporządkowanie naklejek do użytkowników ustawiane jest w [osobnym arkuszu Google](https://docs.google.com/spreadsheets/d/1GCBGiRiw7Pa9nlrnJXxWqHux2EfGCbZXFOB7NL6kq2U/edit?usp=sharing)

## Zasady konfiguracji

0. Pliki konfiguracyjne w tym repozytorium są zapisane w formacie [JSON5](https://json5.org/). Obsługiwane przez Discord formaty plików graficznych to JPG, PNG, GIF, WEBP oraz AVIF.
   Teoretycznie naklejki to mogą być też pliki wideo, audio czy nawet tekstowe, nikt tego nie sprawdza. Ale błagam, nie mówcie tego Radzie...
1. Naklejki mają swoje unikalne identyfikatory. Identyfikatory te "tworzone" są w pliku [stickers.json5](./stickers.json5).
   Identyfikatorów używa się w [arkuszu Google](https://docs.google.com/spreadsheets/d/1GCBGiRiw7Pa9nlrnJXxWqHux2EfGCbZXFOB7NL6kq2U/edit?usp=sharing) celem przypisania naklejek użytkownikom.
   Ponadto w pliku [categories.json5](./categories.json5) kategorie są przyporządkowywane naklejkom na podstawie ich identyfikatorów.
3. Plik [stickers.json5](./stickers.json5) składa się z listy (a właściwie zbioru) naklejek, gdzie każda naklejka określona jest jako obiekt następującej postaci:
   ```json5
   "unikalny_identyfikator_do_wpisania_w_arkusz": {
       path: "pełna ścieżka do pliku grafiki.jpg",
       author: "autor grafiki",
       name: "Domyślna Nazwa Naklejki",  // można dostosować w arkuszu za pomocą notatek przy komórkach
       description: "Domyślny opis naklejki.",  // można dostosować w arkuszu za pomocą notatek przy komórkach
       supersedes: [
           "lista_identyfikatorow",
           "naklejek_ktore_ta_konkretna_naklejka",
           "przykrywa_ukosnik_zastepuje",
       ],
       unlisted: true,  // true, jeśli naklejka ma być pominięta w spisie ogólnych, false w przeciwnym wypadku
   },
   // zostawiamy zawsze "wiszący" przecinek na końcu, żeby nie trzeba było się zastanawiać i żeby ładnie się wyświetlało w GitHub > Pull requests > Files changed
   ```
   Klucze `superseded` oraz `unlisted` są opcjonalne. Domyślne ich wartości to odpowiednio pusta lista oraz `false`.
4. Plik [categories.json5](./categories.json5) to lista kategorii. Składa się z wpisów postaci:
   ```json5
   {
       title: "Tytuł kategorii",
       regex: "wyrażenie regularne (regex) określające, jakie identyfikatory naklejek pasują do tej kategorii",
   },
   // zostawiamy zawsze "wiszący" przecinek na końcu, żeby nie trzeba było się zastanawiać i żeby ładnie się wyświetlało w GitHub > Pull requests > Files changed
   ```  
   Kolejność wpisów ma znaczenie - jeśli naklejka zostanie dopasowana np. do pierwszego, to nie zostanie uwzględniona już w żadnym kolejnym.
   Wyrażenia regularne[^1] można sobie przetestować na stronie [Regex101](https://regex101.com/).
5. Przy uzupełnianiu arkusza należy się kierować instrukcjami w nim zamieszczonymi. Wszystko podzielone jest na odpowiednie kolumny
   \- od lewej unikalny identyfikator użytkownika, wyświetlaną nazwę, jego ID na różnych platformach, no i wreszcie listę naklejek (każda w osobnej kolumnie).
   Do komórek z naklejkami można dopisywać notatki (nie komentarze!), na podstawie których zmieniana jest treść tytułu i/lub opisu naklejki w albumie danego użytkownika.

[^1]: Najważniejsze symbole: `^` to początek nazwy, `$` to koniec nazwy, `.` to dowolny znak, `[a-z]` oznacza dowolny znak spośród małych liter od a do z.  
      Są jeszcze kwantyfikatory: `?` oznacza opcjonalność poprzedniego symbolu, `*` dowolną liczbę jego wystąpień, a `+` co najmniej jedno - np. do `[4-7]+` pasuje `4`, `745`, `7777777`, ale ` ` ani `3` już nie.
      Żeby zamiast specjalnego znaczenia powyższych symboli, należy użyć znaku ucieczki `\`. Np. `\.` to po prostu kropka, a nie dowolny znak.
