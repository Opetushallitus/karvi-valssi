import {ArvoOppilaitos} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';

export function not(a: ArvoOppilaitos[], b: ArvoOppilaitos[]) {
    return a.filter((value) => b.indexOf(value) === -1);
}

export function intersection(a: ArvoOppilaitos[], b: ArvoOppilaitos[]) {
    return a.filter((value) => b.indexOf(value) !== -1);
}

export function union(a: ArvoOppilaitos[], b: ArvoOppilaitos[]) {
    return [...a, ...not(b, a)];
}

export const filterOppilaitos = (
    items: ArvoOppilaitos[],
    keyWord: string,
    lang: string,
) => {
    const oppilaitosNimi = `nimi_${lang}` as keyof ArvoOppilaitos;
    const kw = keyWord.trim().toLowerCase();
    if (kw !== '') {
        return items.filter((item) => item[oppilaitosNimi]?.toLowerCase().includes(kw));
    }
    return items;
};

export const sortOppilaitos = (items: ArvoOppilaitos[], lang: string) => {
    const oppilaitosNimi = `nimi_${lang}` as keyof ArvoOppilaitos;
    return items.sort((a, b) => {
        const aName = a[oppilaitosNimi]?.toLowerCase() || '';
        const bName = b[oppilaitosNimi]?.toLowerCase() || '';
        return aName < bName ? -1 : 1;
    });
};
