var KataLanguages = {
  get: function (langcode, current) {
    var lang = KataLanguages.LANGS[langcode];
    return lang ? lang[current] : langcode;
  },
  LANGS: {
    "aar": {
      "en": "Afar",
      "fi": "afar"
    },
    "abk": {
      "en": "Abkhazian",
      "fi": "abhaasi"
    },
    "ace": {
      "en": "Achinese",
      "fi": "aceh"
    },
    "ach": {
      "en": "Acoli",
      "fi": "atšoli"
    },
    "ada": {
      "en": "Adangme",
      "fi": "adangme"
    },
    "ady": {
      "en": "Adyghe; Adygei",
      "fi": "agyde"
    },
    "afa": {
      "en": "Afro-Asiatic languages",
      "fi": "afroaasialaiset kielet"
    },
    "afh": {
      "en": "Afrihili",
      "fi": "afrihili"
    },
    "afr": {
      "en": "Afrikaans",
      "fi": "afrikaans"
    },
    "ain": {
      "en": "Ainu",
      "fi": "ainu"
    },
    "aka": {
      "en": "Akan",
      "fi": "akan"
    },
    "akk": {
      "en": "Akkadian",
      "fi": "akkadi"
    },
    "ale": {
      "en": "Aleut",
      "fi": "aleutti"
    },
    "alg": {
      "en": "Algonquian languages",
      "fi": "algonkinkielet"
    },
    "alt": {
      "en": "Southern Altai",
      "fi": "eteläaltai"
    },
    "amh": {
      "en": "Amharic",
      "fi": "amhara"
    },
    "ang": {
      "en": "English, Old (ca. 450-1100)",
      "fi": "muinaisenglanti"
    },
    "anp": {
      "en": "Angika",
      "fi": "angika"
    },
    "apa": {
      "en": "Apache languages",
      "fi": "apaššikielet"
    },
    "ara": {
      "en": "Arabic",
      "fi": "arabia"
    },
    "arc": {
      "en": "Official Aramaic (700-300 BCE); Imperial Aramaic (700-300 BCE)",
      "fi": "aramea"
    },
    "arg": {
      "en": "Aragonese",
      "fi": "aragonia"
    },
    "arn": {
      "en": "Mapudungun; Mapuche",
      "fi": "araukaani"
    },
    "arp": {
      "en": "Arapaho",
      "fi": "arapaho"
    },
    "art": {
      "en": "Artificial languages",
      "fi": "keinotekoiset kielet"
    },
    "arw": {
      "en": "Arawak",
      "fi": "arawak"
    },
    "asm": {
      "en": "Assamese",
      "fi": "asami"
    },
    "ast": {
      "en": "Asturian; Bable; Leonese; Asturleonese",
      "fi": "asturia"
    },
    "ath": {
      "en": "Athapascan languages",
      "fi": "athabasca-kielet"
    },
    "aus": {
      "en": "Australian languages",
      "fi": "australialaiset kielet"
    },
    "ava": {
      "en": "Avaric",
      "fi": "avaari"
    },
    "ave": {
      "en": "Avestan",
      "fi": "avestan"
    },
    "awa": {
      "en": "Awadhi",
      "fi": "awadhi"
    },
    "aym": {
      "en": "Aymara",
      "fi": "aymara"
    },
    "aze": {
      "en": "Azerbaijani",
      "fi": "azeri"
    },
    "bad": {
      "en": "Banda languages",
      "fi": "banda"
    },
    "bai": {
      "en": "Bamileke languages",
      "fi": "bamileke-kielet"
    },
    "bak": {
      "en": "Bashkir",
      "fi": "baškiiri"
    },
    "bal": {
      "en": "Baluchi",
      "fi": "belutši"
    },
    "bam": {
      "en": "Bambara",
      "fi": "bambara"
    },
    "ban": {
      "en": "Balinese",
      "fi": "bali"
    },
    "bas": {
      "en": "Basa",
      "fi": "basa"
    },
    "bat": {
      "en": "Baltic languages",
      "fi": "balttilaiset kielet"
    },
    "bej": {
      "en": "Beja; Bedawiyet",
      "fi": "bedža"
    },
    "bel": {
      "en": "Belarusian",
      "fi": "valkovenäjä"
    },
    "bem": {
      "en": "Bemba",
      "fi": "bemba"
    },
    "ben": {
      "en": "Bengali",
      "fi": "bengali"
    },
    "ber": {
      "en": "Berber languages",
      "fi": "berberikielet"
    },
    "bho": {
      "en": "Bhojpuri",
      "fi": "bhojpuri"
    },
    "bih": {
      "en": "Bihari languages",
      "fi": "bihari-kielet"
    },
    "bik": {
      "en": "Bikol",
      "fi": "bikol"
    },
    "bin": {
      "en": "Bini; Edo",
      "fi": "bini"
    },
    "bis": {
      "en": "Bislama",
      "fi": "bislama"
    },
    "bla": {
      "en": "Siksika",
      "fi": "mustajalka (siksika)"
    },
    "bnt": {
      "en": "Bantu languages",
      "fi": "bantukielet"
    },
    "bod": {
      "en": "Tibetan",
      "fi": "tiibetti"
    },
    "bos": {
      "en": "Bosnian",
      "fi": "bosnia"
    },
    "bra": {
      "en": "Braj",
      "fi": "bradž"
    },
    "bre": {
      "en": "Breton",
      "fi": "bretoni"
    },
    "btk": {
      "en": "Batak languages",
      "fi": "batak"
    },
    "bua": {
      "en": "Buriat",
      "fi": "burjaatti"
    },
    "bug": {
      "en": "Buginese",
      "fi": "bugi"
    },
    "bul": {
      "en": "Bulgarian",
      "fi": "bulgaria"
    },
    "byn": {
      "en": "Blin; Bilin",
      "fi": "bilen (bilin, blin)"
    },
    "cad": {
      "en": "Caddo",
      "fi": "caddo"
    },
    "cai": {
      "en": "Central American Indian languages",
      "fi": "Keski-Amerikan intiaanikielet"
    },
    "car": {
      "en": "Galibi Carib",
      "fi": "karibi"
    },
    "cat": {
      "en": "Catalan; Valencian",
      "fi": "katalaani"
    },
    "cau": {
      "en": "Caucasian languages",
      "fi": "kaukasialaiset kielet"
    },
    "ceb": {
      "en": "Cebuano",
      "fi": "cebuano"
    },
    "cel": {
      "en": "Celtic languages",
      "fi": "kelttiläiset kielet"
    },
    "ces": {
      "en": "Czech",
      "fi": "tšekki"
    },
    "cha": {
      "en": "Chamorro",
      "fi": "chamorro"
    },
    "chb": {
      "en": "Chibcha",
      "fi": "chibcha"
    },
    "che": {
      "en": "Chechen",
      "fi": "tšetšeeni"
    },
    "chg": {
      "en": "Chagatai",
      "fi": "tšagatai"
    },
    "chk": {
      "en": "Chuukese",
      "fi": "chuuk"
    },
    "chm": {
      "en": "Mari",
      "fi": "mari"
    },
    "chn": {
      "en": "Chinook jargon",
      "fi": "chinook-jargon"
    },
    "cho": {
      "en": "Choctaw",
      "fi": "choctaw"
    },
    "chp": {
      "en": "Chipewyan; Dene Suline",
      "fi": "chipewyan"
    },
    "chr": {
      "en": "Cherokee",
      "fi": "cherokee"
    },
    "chv": {
      "en": "Chuvash",
      "fi": "tšuvassi"
    },
    "chu": {
      "en": "Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic",
      "fi": "kirkkoslaavi"
    },
    "chy": {
      "en": "Cheyenne",
      "fi": "cheyenne"
    },
    "cmc": {
      "en": "Chamic languages",
      "fi": "cham-kielet"
    },
    "cop": {
      "en": "Coptic",
      "fi": "kopti"
    },
    "cor": {
      "en": "Cornish",
      "fi": "korni"
    },
    "cos": {
      "en": "Corsican",
      "fi": "korsika"
    },
    "cpe": {
      "en": "Creoles and pidgins, English based",
      "fi": "kreolit ja pidginit, englantiin perustuvat"
    },
    "cpf": {
      "en": "Creoles and pidgins, French-based",
      "fi": "kreolit ja pidginit, ranskaan perustuvat"
    },
    "cpp": {
      "en": "Creoles and pidgins, Portuguese-based",
      "fi": "kreolit ja pidginit, portugaliin perustuvat"
    },
    "cre": {
      "en": "Cree",
      "fi": "cree"
    },
    "crh": {
      "en": "Crimean Tatar; Crimean Turkish",
      "fi": "krimintataari; kriminturkki"
    },
    "crp": {
      "en": "Creoles and pidgins",
      "fi": "kreolit ja pidginit"
    },
    "csb": {
      "en": "Kashubian",
      "fi": "kašubi"
    },
    "cus": {
      "en": "Cushitic languages",
      "fi": "kuušilaiset kielet"
    },
    "cym": {
      "en": "Welsh",
      "fi": "kymri"
    },
    "dak": {
      "en": "Dakota",
      "fi": "dakota"
    },
    "dan": {
      "en": "Danish",
      "fi": "tanska"
    },
    "dar": {
      "en": "Dargwa",
      "fi": "dargva"
    },
    "day": {
      "en": "Land Dayak languages",
      "fi": "dajakki"
    },
    "del": {
      "en": "Delaware",
      "fi": "delaware"
    },
    "den": {
      "en": "Slave (Athapascan)",
      "fi": "athapaski-slavi"
    },
    "deu": {
      "en": "German",
      "fi": "saksa"
    },
    "dgr": {
      "en": "Dogrib",
      "fi": "dogrib"
    },
    "din": {
      "en": "Dinka",
      "fi": "dinka"
    },
    "div": {
      "en": "Divehi; Dhivehi; Maldivian",
      "fi": "divehi"
    },
    "doi": {
      "en": "Dogri",
      "fi": "dogri"
    },
    "dra": {
      "en": "Dravidian languages",
      "fi": "dravidakielet"
    },
    "dsb": {
      "en": "Lower Sorbian",
      "fi": "alasorbi"
    },
    "dua": {
      "en": "Duala",
      "fi": "duala"
    },
    "dum": {
      "en": "Dutch, Middle (ca. 1050-1350)",
      "fi": "keskihollanti"
    },
    "dyu": {
      "en": "Dyula",
      "fi": "dyula"
    },
    "dzo": {
      "en": "Dzongkha",
      "fi": "dzongkha"
    },
    "efi": {
      "en": "Efik",
      "fi": "efik"
    },
    "egy": {
      "en": "Egyptian (Ancient)",
      "fi": "muinaisegypti"
    },
    "eka": {
      "en": "Ekajuk",
      "fi": "ekajuk"
    },
    "ell": {
      "en": "Greek, Modern (1453-)",
      "fi": "nykykreikka"
    },
    "elx": {
      "en": "Elamite",
      "fi": "elami"
    },
    "eng": {
      "en": "English",
      "fi": "englanti"
    },
    "enm": {
      "en": "English, Middle (1100-1500)",
      "fi": "keskienglanti"
    },
    "epo": {
      "en": "Esperanto",
      "fi": "esperanto"
    },
    "est": {
      "en": "Estonian",
      "fi": "viro"
    },
    "eus": {
      "en": "Basque",
      "fi": "baski"
    },
    "ewe": {
      "en": "Ewe",
      "fi": "ewe"
    },
    "ewo": {
      "en": "Ewondo",
      "fi": "ewondo"
    },
    "fan": {
      "en": "Fang",
      "fi": "fang"
    },
    "fao": {
      "en": "Faroese",
      "fi": "fääri"
    },
    "fas": {
      "en": "Persian",
      "fi": "persia"
    },
    "fat": {
      "en": "Fanti",
      "fi": "fanti"
    },
    "fij": {
      "en": "Fijian",
      "fi": "fidži"
    },
    "fil": {
      "en": "Filipino; Pilipino",
      "fi": "filippiino"
    },
    "fin": {
      "en": "Finnish",
      "fi": "suomi"
    },
    "fiu": {
      "en": "Finno-Ugrian languages",
      "fi": "suomalais-ugrilaiset kielet"
    },
    "fon": {
      "en": "Fon",
      "fi": "fon"
    },
    "fra": {
      "en": "French",
      "fi": "ranska"
    },
    "frm": {
      "en": "French, Middle (ca. 1400-1600)",
      "fi": "keskiranska"
    },
    "fro": {
      "en": "French, Old (842-ca. 1400)",
      "fi": "muinaisranska"
    },
    "frr": {
      "en": "Northern Frisian",
      "fi": "pohjoisfriisi"
    },
    "frs": {
      "en": "Eastern Frisian",
      "fi": "itäfriisi"
    },
    "fry": {
      "en": "Western Frisian",
      "fi": "länsifriisi"
    },
    "ful": {
      "en": "Fulah",
      "fi": "fulani"
    },
    "fur": {
      "en": "Friulian",
      "fi": "friuli"
    },
    "gaa": {
      "en": "Ga",
      "fi": "gã"
    },
    "gay": {
      "en": "Gayo",
      "fi": "gayo"
    },
    "gba": {
      "en": "Gbaya",
      "fi": "gbaya"
    },
    "gem": {
      "en": "Germanic languages",
      "fi": "germaaniset kielet"
    },
    "gez": {
      "en": "Geez",
      "fi": "ge'ez"
    },
    "gil": {
      "en": "Gilbertese",
      "fi": "kiribati"
    },
    "gla": {
      "en": "Gaelic; Scottish Gaelic",
      "fi": "gaeli"
    },
    "gle": {
      "en": "Irish",
      "fi": "iiri"
    },
    "glg": {
      "en": "Galician",
      "fi": "galicia"
    },
    "glv": {
      "en": "Manx",
      "fi": "manksi"
    },
    "gmh": {
      "en": "German, Middle High (ca. 1050-1500)",
      "fi": "keskiyläsaksa"
    },
    "goh": {
      "en": "German, Old High (ca. 750-1050)",
      "fi": "muinaisyläsaksa"
    },
    "gon": {
      "en": "Gondi",
      "fi": "gondi"
    },
    "gor": {
      "en": "Gorontalo",
      "fi": "gorontalo"
    },
    "got": {
      "en": "Gothic",
      "fi": "gootti"
    },
    "grb": {
      "en": "Grebo",
      "fi": "grebo"
    },
    "grc": {
      "en": "Greek, Ancient (to 1453)",
      "fi": "muinaiskreikka"
    },
    "grn": {
      "en": "Guarani",
      "fi": "guarani"
    },
    "gsw": {
      "en": "Swiss German; Alemannic; Alsatian",
      "fi": "sveitsinsaksa"
    },
    "guj": {
      "en": "Gujarati",
      "fi": "gujarati"
    },
    "gwi": {
      "en": "Gwich'in",
      "fi": "gwitšin"
    },
    "hai": {
      "en": "Haida",
      "fi": "haida"
    },
    "hat": {
      "en": "Haitian; Haitian Creole",
      "fi": "haiti"
    },
    "hau": {
      "en": "Hausa",
      "fi": "hausa"
    },
    "haw": {
      "en": "Hawaiian",
      "fi": "havaiji"
    },
    "heb": {
      "en": "Hebrew",
      "fi": "heprea"
    },
    "her": {
      "en": "Herero",
      "fi": "herero"
    },
    "hil": {
      "en": "Hiligaynon",
      "fi": "hiligaynon"
    },
    "him": {
      "en": "Himachali languages; Western Pahari languages",
      "fi": "Himachal-kielet; läntiset pahari-kielet"
    },
    "hin": {
      "en": "Hindi",
      "fi": "hindi"
    },
    "hit": {
      "en": "Hittite",
      "fi": "heetti"
    },
    "hmn": {
      "en": "Hmong; Mong",
      "fi": "hmong; mong"
    },
    "hmo": {
      "en": "Hiri Motu",
      "fi": "hiri-motu"
    },
    "hrv": {
      "en": "Croatian",
      "fi": "kroatia"
    },
    "hsb": {
      "en": "Upper Sorbian",
      "fi": "yläsorbi"
    },
    "hun": {
      "en": "Hungarian",
      "fi": "unkari"
    },
    "hup": {
      "en": "Hupa",
      "fi": "hupa"
    },
    "hye": {
      "en": "Armenian",
      "fi": "armenia"
    },
    "iba": {
      "en": "Iban",
      "fi": "iban"
    },
    "ibo": {
      "en": "Igbo",
      "fi": "igbo"
    },
    "ido": {
      "en": "Ido",
      "fi": "ido"
    },
    "iii": {
      "en": "Sichuan Yi; Nuosu",
      "fi": "sichuanin-yi"
    },
    "ijo": {
      "en": "Ijo languages",
      "fi": "idžo"
    },
    "iku": {
      "en": "Inuktitut",
      "fi": "inuktitut"
    },
    "ile": {
      "en": "Interlingue; Occidental",
      "fi": "interlingue"
    },
    "ilo": {
      "en": "Iloko",
      "fi": "iloko"
    },
    "ina": {
      "en": "Interlingua (International Auxiliary Language Association)",
      "fi": "interlingua"
    },
    "inc": {
      "en": "Indic languages",
      "fi": "indoarjalaiset kielet"
    },
    "ind": {
      "en": "Indonesian",
      "fi": "indonesia"
    },
    "ine": {
      "en": "Indo-European languages",
      "fi": "indoeurooppalaiset kielet"
    },
    "inh": {
      "en": "Ingush",
      "fi": "inguuši"
    },
    "ipk": {
      "en": "Inupiaq",
      "fi": "iñupiaq"
    },
    "ira": {
      "en": "Iranian languages",
      "fi": "iranilaiset kielet"
    },
    "iro": {
      "en": "Iroquoian languages",
      "fi": "irokeesikielet"
    },
    "isl": {
      "en": "Icelandic",
      "fi": "islanti"
    },
    "ita": {
      "en": "Italian",
      "fi": "italia"
    },
    "jav": {
      "en": "Javanese",
      "fi": "jaava"
    },
    "jbo": {
      "en": "Lojban",
      "fi": "lojban"
    },
    "jpn": {
      "en": "Japanese",
      "fi": "japani"
    },
    "jpr": {
      "en": "Judeo-Persian",
      "fi": "juutalaispersia"
    },
    "jrb": {
      "en": "Judeo-Arabic",
      "fi": "juutalaisarabia"
    },
    "kaa": {
      "en": "Kara-Kalpak",
      "fi": "karakalpakki"
    },
    "kab": {
      "en": "Kabyle",
      "fi": "kabyyli"
    },
    "kac": {
      "en": "Kachin; Jingpho",
      "fi": "kachin"
    },
    "kal": {
      "en": "Kalaallisut; Greenlandic",
      "fi": "kalaallisut; grönlanti"
    },
    "kam": {
      "en": "Kamba",
      "fi": "kamba"
    },
    "kan": {
      "en": "Kannada",
      "fi": "kannada"
    },
    "kar": {
      "en": "Karen languages",
      "fi": "karen"
    },
    "kas": {
      "en": "Kashmiri",
      "fi": "kashmiri"
    },
    "kat": {
      "en": "Georgian",
      "fi": "georgia"
    },
    "kau": {
      "en": "Kanuri",
      "fi": "kanuri"
    },
    "kaw": {
      "en": "Kawi",
      "fi": "kavi"
    },
    "kaz": {
      "en": "Kazakh",
      "fi": "kazakki"
    },
    "kbd": {
      "en": "Kabardian",
      "fi": "kabardi"
    },
    "kha": {
      "en": "Khasi",
      "fi": "khasi"
    },
    "khi": {
      "en": "Khoisan languages",
      "fi": "khoisan-kielet"
    },
    "khm": {
      "en": "Central Khmer",
      "fi": "khmer"
    },
    "kho": {
      "en": "Khotanese;Sakan",
      "fi": "khotani"
    },
    "kik": {
      "en": "Kikuyu; Gikuyu",
      "fi": "kikuju"
    },
    "kin": {
      "en": "Kinyarwanda",
      "fi": "ruanda"
    },
    "kir": {
      "en": "Kirghiz; Kyrgyz",
      "fi": "kirgiisi"
    },
    "kmb": {
      "en": "Kimbundu",
      "fi": "kimbundu"
    },
    "kok": {
      "en": "Konkani",
      "fi": "konkani"
    },
    "kom": {
      "en": "Komi",
      "fi": "komi"
    },
    "kon": {
      "en": "Kongo",
      "fi": "kongo"
    },
    "kor": {
      "en": "Korean",
      "fi": "korea"
    },
    "kos": {
      "en": "Kosraean",
      "fi": "kosrae"
    },
    "kpe": {
      "en": "Kpelle",
      "fi": "kpelle"
    },
    "krc": {
      "en": "Karachay-Balkar",
      "fi": "karatšai-balkaari"
    },
    "krl": {
      "en": "Karelian",
      "fi": "karjala"
    },
    "kro": {
      "en": "Kru languages",
      "fi": "kru-kielet"
    },
    "kru": {
      "en": "Kurukh",
      "fi": "kurukh"
    },
    "kua": {
      "en": "Kuanyama; Kwanyama",
      "fi": "kuanjama"
    },
    "kum": {
      "en": "Kumyk",
      "fi": "kumykki"
    },
    "kur": {
      "en": "Kurdish",
      "fi": "kurdi"
    },
    "kut": {
      "en": "Kutenai",
      "fi": "kutenai"
    },
    "lad": {
      "en": "Ladino",
      "fi": "ladino"
    },
    "lah": {
      "en": "Lahnda",
      "fi": "lahnda"
    },
    "lam": {
      "en": "Lamba",
      "fi": "lamba"
    },
    "lao": {
      "en": "Lao",
      "fi": "lao"
    },
    "lat": {
      "en": "Latin",
      "fi": "latina"
    },
    "lav": {
      "en": "Latvian",
      "fi": "latvia"
    },
    "lez": {
      "en": "Lezghian",
      "fi": "lezgi"
    },
    "lim": {
      "en": "Limburgan; Limburger; Limburgish",
      "fi": "limburg"
    },
    "lin": {
      "en": "Lingala",
      "fi": "lingala"
    },
    "lit": {
      "en": "Lithuanian",
      "fi": "liettua"
    },
    "lol": {
      "en": "Mongo",
      "fi": "mongo"
    },
    "loz": {
      "en": "Lozi",
      "fi": "lozi"
    },
    "ltz": {
      "en": "Luxembourgish; Letzeburgesch",
      "fi": "luxemburg"
    },
    "lua": {
      "en": "Luba-Lulua",
      "fi": "luba (Lulua)"
    },
    "lub": {
      "en": "Luba-Katanga",
      "fi": "luba (Katanga)"
    },
    "lug": {
      "en": "Ganda",
      "fi": "ganda"
    },
    "lui": {
      "en": "Luiseno",
      "fi": "luiseño"
    },
    "lun": {
      "en": "Lunda",
      "fi": "lunda"
    },
    "luo": {
      "en": "Luo (Kenya and Tanzania)",
      "fi": "luo"
    },
    "lus": {
      "en": "Lushai",
      "fi": "lushai"
    },
    "mad": {
      "en": "Madurese",
      "fi": "madura"
    },
    "mag": {
      "en": "Magahi",
      "fi": "magahi"
    },
    "mah": {
      "en": "Marshallese",
      "fi": "marshallinsaaret"
    },
    "mai": {
      "en": "Maithili",
      "fi": "maithili"
    },
    "mak": {
      "en": "Makasar",
      "fi": "makassar"
    },
    "mal": {
      "en": "Malayalam",
      "fi": "malayalam"
    },
    "man": {
      "en": "Mandingo",
      "fi": "mandingo"
    },
    "map": {
      "en": "Austronesian languages",
      "fi": "austronesialaiset kielet"
    },
    "mar": {
      "en": "Marathi",
      "fi": "marathi"
    },
    "mas": {
      "en": "Masai",
      "fi": "masai"
    },
    "mdf": {
      "en": "Moksha",
      "fi": "mokša"
    },
    "mdr": {
      "en": "Mandar",
      "fi": "mandar"
    },
    "men": {
      "en": "Mende",
      "fi": "mende"
    },
    "mga": {
      "en": "Irish, Middle (900-1200)",
      "fi": "keski-iiri"
    },
    "mic": {
      "en": "Mi'kmaq; Micmac",
      "fi": "micmac"
    },
    "min": {
      "en": "Minangkabau",
      "fi": "minangkabau"
    },
    "mis": {
      "en": "Uncoded languages",
      "fi": "kooditon kieli"
    },
    "mkd": {
      "en": "Macedonian",
      "fi": "makedonia"
    },
    "mkh": {
      "en": "Mon-Khmer languages",
      "fi": "mon-khmer-kielet"
    },
    "mlg": {
      "en": "Malagasy",
      "fi": "malagassi"
    },
    "mlt": {
      "en": "Maltese",
      "fi": "malta"
    },
    "mnc": {
      "en": "Manchu",
      "fi": "mantšu"
    },
    "mni": {
      "en": "Manipuri",
      "fi": "manipuri"
    },
    "mno": {
      "en": "Manobo languages",
      "fi": "manobokielet"
    },
    "moh": {
      "en": "Mohawk",
      "fi": "mohawk"
    },
    "mol": {
      "en": "Moldavian; Moldovan",
      "fi": "moldavia"
    },
    "mon": {
      "en": "Mongolian",
      "fi": "mongoli"
    },
    "mos": {
      "en": "Mossi",
      "fi": "mossi"
    },
    "mri": {
      "en": "Maori",
      "fi": "maori"
    },
    "msa": {
      "en": "Malay",
      "fi": "malaiji"
    },
    "mul": {
      "en": "Multiple languages",
      "fi": "monia kieliä"
    },
    "mun": {
      "en": "Munda languages",
      "fi": "mundakielet"
    },
    "mus": {
      "en": "Creek",
      "fi": "muskogi"
    },
    "mwl": {
      "en": "Mirandese",
      "fi": "mirandês"
    },
    "mwr": {
      "en": "Marwari",
      "fi": "marwari"
    },
    "mya": {
      "en": "Burmese",
      "fi": "burma"
    },
    "myn": {
      "en": "Mayan languages",
      "fi": "mayakielet"
    },
    "myv": {
      "en": "Erzya",
      "fi": "ersä"
    },
    "nah": {
      "en": "Nahuatl languages",
      "fi": "nahuatl"
    },
    "nai": {
      "en": "North American Indian languages",
      "fi": "Pohjois-Amerikan intiaanikielet"
    },
    "nap": {
      "en": "Neapolitan",
      "fi": "napoli"
    },
    "nau": {
      "en": "Nauru",
      "fi": "nauru"
    },
    "nav": {
      "en": "Navajo; Navaho",
      "fi": "navajo"
    },
    "nbl": {
      "en": "Ndebele, South; South Ndebele",
      "fi": "ndebele, etelä-"
    },
    "nde": {
      "en": "Ndebele, North; North Ndebele",
      "fi": "ndebele, pohjois-"
    },
    "ndo": {
      "en": "Ndonga",
      "fi": "ndonga"
    },
    "nds": {
      "en": "Low German; Low Saxon; German, Low; Saxon, Low",
      "fi": "alasaksa"
    },
    "nep": {
      "en": "Nepali",
      "fi": "nepali"
    },
    "new": {
      "en": "Nepal Bhasa; Newari",
      "fi": "newari"
    },
    "nia": {
      "en": "Nias",
      "fi": "nias"
    },
    "nic": {
      "en": "Niger-Kordofanian languages",
      "fi": "nigeriläis-kongolaiset kielet"
    },
    "niu": {
      "en": "Niuean",
      "fi": "niue"
    },
    "nld": {
      "en": "Dutch; Flemish",
      "fi": "hollanti"
    },
    "nno": {
      "en": "Norwegian Nynorsk; Nynorsk, Norwegian",
      "fi": "norja (nynorsk)"
    },
    "nob": {
      "en": "Bokmål, Norwegian; Norwegian Bokmål",
      "fi": "norja (bokmål)"
    },
    "nog": {
      "en": "Nogai",
      "fi": "nogai"
    },
    "non": {
      "en": "Norse, Old",
      "fi": "muinaisnorja"
    },
    "nor": {
      "en": "Norwegian",
      "fi": "norja"
    },
    "nqo": {
      "en": "N'Ko",
      "fi": "n'ko"
    },
    "nso": {
      "en": "Pedi; Sepedi; Northern Sotho",
      "fi": "pohjoissotho"
    },
    "nub": {
      "en": "Nubian languages",
      "fi": "nubialaiset kielet"
    },
    "nwc": {
      "en": "Classical Newari; Old Newari; Classical Nepal Bhasa",
      "fi": "klassinen newari"
    },
    "nya": {
      "en": "Chichewa; Chewa; Nyanja",
      "fi": "nyanja (chewa)"
    },
    "nym": {
      "en": "Nyamwezi",
      "fi": "nyamwezi"
    },
    "nyn": {
      "en": "Nyankole",
      "fi": "nyankole"
    },
    "nyo": {
      "en": "Nyoro",
      "fi": "nyoro"
    },
    "nzi": {
      "en": "Nzima",
      "fi": "nzima"
    },
    "oci": {
      "en": "Occitan (post 1500)",
      "fi": "oksitaani"
    },
    "oji": {
      "en": "Ojibwa",
      "fi": "odžibwa"
    },
    "ori": {
      "en": "Oriya",
      "fi": "oriya"
    },
    "orm": {
      "en": "Oromo",
      "fi": "oromo"
    },
    "osa": {
      "en": "Osage",
      "fi": "osage"
    },
    "oss": {
      "en": "Ossetian; Ossetic",
      "fi": "osseetti"
    },
    "ota": {
      "en": "Turkish, Ottoman (1500-1928)",
      "fi": "osmaninturkki"
    },
    "oto": {
      "en": "Otomian languages",
      "fi": "otomikielet"
    },
    "paa": {
      "en": "Papuan languages",
      "fi": "papualaiset kielet"
    },
    "pag": {
      "en": "Pangasinan",
      "fi": "pangasinan"
    },
    "pal": {
      "en": "Pahlavi",
      "fi": "pahlavi"
    },
    "pam": {
      "en": "Pampanga; Kapampangan",
      "fi": "pampanga"
    },
    "pan": {
      "en": "Panjabi; Punjabi",
      "fi": "panjabi"
    },
    "pap": {
      "en": "Papiamento",
      "fi": "papiamentu"
    },
    "pau": {
      "en": "Palauan",
      "fi": "palau"
    },
    "peo": {
      "en": "Persian, Old (ca. 600-400 B.C.)",
      "fi": "muinaispersia"
    },
    "phi": {
      "en": "Philippine languages",
      "fi": "filippiiniläiset kielet"
    },
    "phn": {
      "en": "Phoenician",
      "fi": "foinikia"
    },
    "pli": {
      "en": "Pali",
      "fi": "paali"
    },
    "pol": {
      "en": "Polish",
      "fi": "puola"
    },
    "pon": {
      "en": "Pohnpeian",
      "fi": "pohnpei"
    },
    "por": {
      "en": "Portuguese",
      "fi": "portugali"
    },
    "pra": {
      "en": "Prakrit languages",
      "fi": "prakrit-kielet"
    },
    "pro": {
      "en": "Provençal, Old (to 1500); Occitan, Old (to 1500)",
      "fi": "muinaisprovensaali"
    },
    "pus": {
      "en": "Pushto; Pashto",
      "fi": "pašto"
    },
    "que": {
      "en": "Quechua",
      "fi": "ketšua"
    },
    "raj": {
      "en": "Rajasthani",
      "fi": "rajasthani"
    },
    "rap": {
      "en": "Rapanui",
      "fi": "rapanui"
    },
    "rar": {
      "en": "Rarotongan; Cook Islands Maori",
      "fi": "rarotonga"
    },
    "roa": {
      "en": "Romance languages",
      "fi": "romaaniset kielet"
    },
    "roh": {
      "en": "Romansh",
      "fi": "retoromaani"
    },
    "rom": {
      "en": "Romany",
      "fi": "romani"
    },
    "ron": {
      "en": "Romanian",
      "fi": "romania"
    },
    "run": {
      "en": "Rundi",
      "fi": "rundi"
    },
    "rup": {
      "en": "Aromanian; Arumanian; Macedo-Romanian",
      "fi": "aromaani"
    },
    "rus": {
      "en": "Russian",
      "fi": "venäjä"
    },
    "sad": {
      "en": "Sandawe",
      "fi": "sandawe"
    },
    "sag": {
      "en": "Sango",
      "fi": "sango"
    },
    "sah": {
      "en": "Yakut",
      "fi": "jakuutti"
    },
    "sai": {
      "en": "South American Indian languages",
      "fi": "Etelä-Amerikan intiaanikielet"
    },
    "sal": {
      "en": "Salishan languages",
      "fi": "sališilaiset kielet"
    },
    "sam": {
      "en": "Samaritan Aramaic",
      "fi": "samarianaramea"
    },
    "san": {
      "en": "Sanskrit",
      "fi": "sanskrit"
    },
    "sas": {
      "en": "Sasak",
      "fi": "sasak"
    },
    "sat": {
      "en": "Santali",
      "fi": "santali"
    },
    "scn": {
      "en": "Sicilian",
      "fi": "sisilia"
    },
    "sco": {
      "en": "Scots",
      "fi": "skotti"
    },
    "sel": {
      "en": "Selkup",
      "fi": "selkuppi"
    },
    "sem": {
      "en": "Semitic languages",
      "fi": "seemiläiset kielet"
    },
    "sga": {
      "en": "Irish, Old (to 900)",
      "fi": "muinaisiiri"
    },
    "sgn": {
      "en": "Sign Languages",
      "fi": "viittomakielet"
    },
    "shn": {
      "en": "Shan",
      "fi": "shan"
    },
    "sid": {
      "en": "Sidamo",
      "fi": "sidamo"
    },
    "sin": {
      "en": "Sinhala; Sinhalese",
      "fi": "sinhala"
    },
    "sio": {
      "en": "Siouan languages",
      "fi": "sioux-kielet"
    },
    "sit": {
      "en": "Sino-Tibetan languages",
      "fi": "sinotiibetiläiset kielet"
    },
    "sla": {
      "en": "Slavic languages",
      "fi": "slaavilaiset kielet"
    },
    "slk": {
      "en": "Slovak",
      "fi": "slovakki"
    },
    "slv": {
      "en": "Slovenian",
      "fi": "sloveeni"
    },
    "sma": {
      "en": "Southern Sami",
      "fi": "eteläsaame"
    },
    "sme": {
      "en": "Northern Sami",
      "fi": "pohjoissaame"
    },
    "smi": {
      "en": "Sami languages",
      "fi": "saamelaiskielet"
    },
    "smj": {
      "en": "Lule Sami",
      "fi": "luulajansaame"
    },
    "smn": {
      "en": "Inari Sami",
      "fi": "inarinsaame"
    },
    "smo": {
      "en": "Samoan",
      "fi": "samoa"
    },
    "sms": {
      "en": "Skolt Sami",
      "fi": "koltansaame"
    },
    "sna": {
      "en": "Shona",
      "fi": "shona"
    },
    "snd": {
      "en": "Sindhi",
      "fi": "sindhi"
    },
    "snk": {
      "en": "Soninke",
      "fi": "soninke"
    },
    "sog": {
      "en": "Sogdian",
      "fi": "sogdi"
    },
    "som": {
      "en": "Somali",
      "fi": "somali"
    },
    "son": {
      "en": "Songhai languages",
      "fi": "songhai"
    },
    "sot": {
      "en": "Sotho, Southern",
      "fi": "eteläsotho"
    },
    "spa": {
      "en": "Spanish; Castilian",
      "fi": "espanja"
    },
    "sqi": {
      "en": "Albanian",
      "fi": "albania"
    },
    "srd": {
      "en": "Sardinian",
      "fi": "sardi"
    },
    "srn": {
      "en": "Sranan Tongo",
      "fi": "Sranan tongo"
    },
    "srp": {
      "en": "Serbian",
      "fi": "serbia"
    },
    "srr": {
      "en": "Serer",
      "fi": "serer"
    },
    "ssa": {
      "en": "Nilo-Saharan languages",
      "fi": "nilosaharalaiset kielet"
    },
    "ssw": {
      "en": "Swati",
      "fi": "swazi"
    },
    "suk": {
      "en": "Sukuma",
      "fi": "sukuma"
    },
    "sun": {
      "en": "Sundanese",
      "fi": "sunda"
    },
    "sus": {
      "en": "Susu",
      "fi": "susu"
    },
    "sux": {
      "en": "Sumerian",
      "fi": "sumeri"
    },
    "swa": {
      "en": "Swahili",
      "fi": "swahili"
    },
    "swe": {
      "en": "Swedish",
      "fi": "ruotsi"
    },
    "syc": {
      "en": "Classical Syriac",
      "fi": "klassinen syyria"
    },
    "syr": {
      "en": "Syriac",
      "fi": "syyria"
    },
    "tah": {
      "en": "Tahitian",
      "fi": "tahiti"
    },
    "tai": {
      "en": "Tai languages",
      "fi": "tai-kielet"
    },
    "tam": {
      "en": "Tamil",
      "fi": "tamili"
    },
    "tat": {
      "en": "Tatar",
      "fi": "tataari"
    },
    "tel": {
      "en": "Telugu",
      "fi": "telugu"
    },
    "tem": {
      "en": "Timne",
      "fi": "temne"
    },
    "ter": {
      "en": "Tereno",
      "fi": "tereno"
    },
    "tet": {
      "en": "Tetum",
      "fi": "tetum"
    },
    "tgk": {
      "en": "Tajik",
      "fi": "tadžikki"
    },
    "tgl": {
      "en": "Tagalog",
      "fi": "tagalog"
    },
    "tha": {
      "en": "Thai",
      "fi": "thai"
    },
    "tig": {
      "en": "Tigre",
      "fi": "tigre"
    },
    "tir": {
      "en": "Tigrinya",
      "fi": "tigrinya"
    },
    "tiv": {
      "en": "Tiv",
      "fi": "tiv"
    },
    "tkl": {
      "en": "Tokelau",
      "fi": "tokelau"
    },
    "tlh": {
      "en": "Klingon; tlhIngan-Hol",
      "fi": "klingon"
    },
    "tli": {
      "en": "Tlingit",
      "fi": "tlinglit"
    },
    "tmh": {
      "en": "Tamashek",
      "fi": "tamashek"
    },
    "tog": {
      "en": "Tonga (Nyasa)",
      "fi": "Malawin tonga"
    },
    "ton": {
      "en": "Tonga (Tonga Islands)",
      "fi": "Tongan tonga"
    },
    "tpi": {
      "en": "Tok Pisin",
      "fi": "tok-pisin"
    },
    "tsi": {
      "en": "Tsimshian",
      "fi": "tsimshian"
    },
    "tsn": {
      "en": "Tswana",
      "fi": "tswana"
    },
    "tso": {
      "en": "Tsonga",
      "fi": "tsonga"
    },
    "tuk": {
      "en": "Turkmen",
      "fi": "turkmeeni"
    },
    "tum": {
      "en": "Tumbuka",
      "fi": "tumbuka"
    },
    "tup": {
      "en": "Tupi languages",
      "fi": "tupikielet"
    },
    "tur": {
      "en": "Turkish",
      "fi": "turkki"
    },
    "tut": {
      "en": "Altaic languages",
      "fi": "altailaiset kielet"
    },
    "tvl": {
      "en": "Tuvalu",
      "fi": "tuvalu"
    },
    "twi": {
      "en": "Twi",
      "fi": "twi"
    },
    "tyv": {
      "en": "Tuvinian",
      "fi": "tuva"
    },
    "udm": {
      "en": "Udmurt",
      "fi": "udmurtti"
    },
    "uga": {
      "en": "Ugaritic",
      "fi": "ugarit"
    },
    "uig": {
      "en": "Uighur; Uyghur",
      "fi": "uiguuri"
    },
    "ukr": {
      "en": "Ukrainian",
      "fi": "ukraina"
    },
    "umb": {
      "en": "Umbundu",
      "fi": "umbundu"
    },
    "und": {
      "en": "Undetermined",
      "fi": "määrittämätön"
    },
    "urd": {
      "en": "Urdu",
      "fi": "urdu"
    },
    "uzb": {
      "en": "Uzbek",
      "fi": "uzbekki"
    },
    "vai": {
      "en": "Vai",
      "fi": "vai"
    },
    "ven": {
      "en": "Venda",
      "fi": "venda"
    },
    "vie": {
      "en": "Vietnamese",
      "fi": "vietnam"
    },
    "vol": {
      "en": "Volapük",
      "fi": "volapük"
    },
    "vot": {
      "en": "Votic",
      "fi": "vatja"
    },
    "wak": {
      "en": "Wakashan languages",
      "fi": "wakashkielet"
    },
    "wal": {
      "en": "Wolaitta; Wolaytta",
      "fi": "wolaytta"
    },
    "war": {
      "en": "Waray",
      "fi": "waray"
    },
    "was": {
      "en": "Washo",
      "fi": "washo"
    },
    "wen": {
      "en": "Sorbian languages",
      "fi": "sorbi"
    },
    "wln": {
      "en": "Walloon",
      "fi": "valloni"
    },
    "wol": {
      "en": "Wolof",
      "fi": "wolof"
    },
    "xal": {
      "en": "Kalmyk; Oirat",
      "fi": "kalmukki"
    },
    "xho": {
      "en": "Xhosa",
      "fi": "xhosa"
    },
    "yao": {
      "en": "Yao",
      "fi": "mien"
    },
    "yap": {
      "en": "Yapese",
      "fi": "yap"
    },
    "yid": {
      "en": "Yiddish",
      "fi": "jiddiš"
    },
    "yor": {
      "en": "Yoruba",
      "fi": "yoruba"
    },
    "ypk": {
      "en": "Yupik languages",
      "fi": "jupikkikielet"
    },
    "zap": {
      "en": "Zapotec",
      "fi": "sapoteekki"
    },
    "zbl": {
      "en": "Blissymbols; Blissymbolics; Bliss",
      "fi": "Bliss-symbolit"
    },
    "zen": {
      "en": "Zenaga",
      "fi": "zenaga"
    },
    "zgh": {
      "en": "Standard Moroccan Tamazight",
      "fi": ""
    },
    "zha": {
      "en": "Zhuang; Chuang",
      "fi": "zhuang"
    },
    "zho": {
      "en": "Chinese",
      "fi": "kiina"
    },
    "znd": {
      "en": "Zande languages",
      "fi": "zande"
    },
    "zul": {
      "en": "Zulu",
      "fi": "zulu"
    },
    "zun": {
      "en": "Zuni",
      "fi": "zuni"
    },
    "zxx": {
      "en": "No linguistic content; Not applicable",
      "fi": "ei kielellistä sisältöä; ei sovellu"
    },
    "zza": {
      "en": "Zaza; Dimili; Dimli; Kirdki; Kirmanjki; Zazaki",
      "fi": "zaza; dimili; dimli; kirdki; kirmanjki; zazaki"
    }
  }
};
