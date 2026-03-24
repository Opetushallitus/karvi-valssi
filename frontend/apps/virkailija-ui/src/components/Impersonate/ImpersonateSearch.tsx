import React, {Dispatch, SetStateAction, useEffect, useMemo, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {Observable} from 'rxjs';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';

import {
    ArvoKoulutustoimija,
    ArvoImpersonoitava,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';

import styles from './AutoComplete.module.css';

function instanceOfArvoKoulutustoimija(object: any): object is ArvoKoulutustoimija {
    return 'nimi_fi' in object;
}

type SearchItem = ArvoImpersonoitava | ArvoKoulutustoimija;

interface ImpersonateSearchProps {
    translationNs: string;
    setOid: Dispatch<SetStateAction<string | null>>;
    fetchFn: (keyword: string) => Observable<SearchItem[]>;
    filterFn?: (obj: any) => boolean;
}

function ImpersonateSearch({
    translationNs = 'impersonointi',
    setOid,
    fetchFn,
    filterFn,
}: ImpersonateSearchProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation([translationNs]);
    const [value, setValue] = useState<SearchItem | null>(null);
    const [inputValue, setInputValue] = useState('');
    const [options, setOptions] = useState<readonly SearchItem[]>([]);
    const koulutustoimijaNimi = `nimi_${lang}` as keyof ArvoKoulutustoimija;

    // Johda tyhjän syötteen lista renderiin: ei tarvita setStatea efektiin
    const baseOptions = useMemo<readonly SearchItem[]>(
        () => (value ? [value] : []),
        [value],
    );

    // Debouncaa syöte yksinkertaisella timeoutilla
    const [debouncedInput, setDebouncedInput] = useState(inputValue);
    useEffect(() => {
        const id = setTimeout(() => setDebouncedInput(inputValue), 400);
        return () => clearTimeout(id);
    }, [inputValue]);

    // Hae, kun debouncattu syöte ei ole tyhjä; tila päivittyy vain async‑callbackissa
    useEffect(() => {
        if (!debouncedInput) return; // tyhjällä syötteellä käytetään baseOptionsia
        const sub = fetchFn(debouncedInput).subscribe({
            next: (results) => {
                const filtered = filterFn ? results.filter(filterFn) : results;
                setOptions(value ? [value, ...filtered] : filtered);
            },
            error: () => {
                // halutessasi: jätä entiset optionsit tai palauta baseOptions
            },
        });
        return () => sub.unsubscribe();
    }, [debouncedInput, value, fetchFn, filterFn]);

    return (
        <Autocomplete
            className={styles['autocomplete-root']}
            id="valssi-autocomplete"
            sx={{width: 600}}
            getOptionLabel={(option) =>
                instanceOfArvoKoulutustoimija(option)
                    ? option[koulutustoimijaNimi]
                    : option.nimi
            }
            filterOptions={(x) => x}
            // Tyhjällä syötteellä käytetään derivoitua listaa, muuten haun tuloksia
            options={inputValue === '' ? baseOptions : options}
            autoComplete
            includeInputInList
            filterSelectedOptions
            value={value}
            noOptionsText={t('ei-hakutuloksia')}
            onChange={(event: any, newValue: SearchItem | null) => {
                // saa jäädä: event‑handlerissa setState on ok
                setOptions((prev) => (newValue ? [newValue, ...prev] : prev));
                setValue(newValue);
                setOid(newValue?.oid ? newValue.oid : null);
            }}
            onInputChange={(event, newInputValue) => {
                setInputValue(newInputValue);
            }}
            renderInput={(props) => (
                <>
                    <label htmlFor="valssi-autocomplete" className="label-for-inputfield">
                        {t('etsi-label')}
                    </label>
                    <TextField {...props} placeholder={t('etsi-placeholder')} fullWidth />
                </>
            )}
            renderOption={(props, option) => (
                <li {...props}>
                    <Grid container alignItems="center">
                        <Grid item sx={{wordWrap: 'break-word'}}>
                            <Box component="span">
                                {instanceOfArvoKoulutustoimija(option)
                                    ? option[koulutustoimijaNimi]
                                    : option.nimi}
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                                {option.oid}
                            </Typography>
                        </Grid>
                    </Grid>
                </li>
            )}
        />
    );
}

export default ImpersonateSearch;
