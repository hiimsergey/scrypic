# Scrypic
A lean Python script to fetch artworks for your MtG decks from [Scryfall](https://scryfall.com).

It uses decks in the MtG Arena format, like this:

```
1 Lightning Bolt
1 Llanowar Elves
1 Opt
...
```

The fetching logic supports Scryfall's filtering syntax, so check out their [syntax guide](https://scryfall.com/docs/syntax).

## Example usage

> [!NOTE]
> This script works with stdin (standard input) and treats your deck as a string.
>
> If your deck is in a file, you use either method:
> 
> `./scrypic.py [options] < deck.txt`
> 
> `cat deck.txt | ./scrypic.py [options]`
>
> If you're in Bash or a Bash-compliant shell and the deck is in a string, you can do this:
> 
> `./scrypic.py [options] <<< "1 Lightning Bolt ..."`

### Latest printings of each card into directory "pngs"
```sh
./scrypic.py pngs/ < deck.txt 
```

### All printings of each card
```sh
./scrypic.py pngs/ "++" < deck.txt
```

### If a card has extended art, take it, otherwise the normal printings
```sh
./scrypic.py pngs/ "++" --prefer "is:full" < deck.txt
```

### Only prints from the MtG Foundations set
```sh
./scrypic.py pngs/ "++ set:fdn" < deck.txt
```

### Download card printings and their related full-art tokens too
```sh
./scrypic.py pngs/ --tokens="is:full" < deck.txt
```

## Only include in-universe cards with the 2015 style border and exclude MTGO or Arena printings
```sh
./scrypic.py pngs/ "not:universesbeyond frame:2015 game:paper" < deck.txt
```
