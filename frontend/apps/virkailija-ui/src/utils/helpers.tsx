import {Kayttoraja} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {
    OppilaitosSetType,
    OppilaitosType,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {TextType} from '@cscfi/shared/services/Data/Data-service';

export const getDefaultEmptySet = (): OppilaitosSetType => ({
    grouped: [],
    ungrouped: [{id: null, name: {fi: '', sv: ''}, oppilaitokset: []}],
});

export function not(a: OppilaitosType[], b: OppilaitosType[]) {
    return a.filter((value) => b.indexOf(value) === -1);
}

export function intersection(a: OppilaitosType[], b: OppilaitosType[]) {
    return a.filter((value) => b.indexOf(value) !== -1);
}

export function union(a: OppilaitosType[], b: OppilaitosType[]) {
    return [...a, ...not(b, a)];
}

export function itemsNot(a: OppilaitosSetType, b: OppilaitosSetType) {
    const newSet: OppilaitosSetType = getDefaultEmptySet();

    newSet.grouped = a.grouped.map((groupA) => {
        const groupB = b.grouped.find((gb) => gb.id === groupA.id);
        if (!groupB) return groupA;
        return {
            ...groupA,
            oppilaitokset: not(groupA.oppilaitokset, groupB.oppilaitokset),
        };
    });

    newSet.ungrouped[0].oppilaitokset = not(
        a.ungrouped[0].oppilaitokset,
        b.ungrouped[0].oppilaitokset,
    );

    return newSet;
}

export function itemsLength(a: OppilaitosSetType) {
    return (
        a.grouped
            .map((group) => group.oppilaitokset.length)
            .reduce((accumulator, currentValue) => accumulator + currentValue, 0) +
        (a.ungrouped[0]?.oppilaitokset.length || 0)
    );
}

export function filterOppilaitosSetByOid(set: OppilaitosSetType, oidList: string[]) {
    const newSet = getDefaultEmptySet();

    newSet.grouped = set.grouped.map((group) => ({
        ...group,
        oppilaitokset: group.oppilaitokset.filter((ol) => oidList.includes(ol.oid)),
    }));

    newSet.grouped = newSet.grouped.filter((group) => group.oppilaitokset.length > 0);

    newSet.ungrouped[0].oppilaitokset = set.ungrouped[0].oppilaitokset.filter((ol) =>
        oidList.includes(ol.oid),
    );

    return newSet;
}

export const hasKayttoraja = (kayttorajaData: Kayttoraja[], kysymysryhmaid: number) => {
    const kayttoraja = kayttorajaData.find((kr) => kr.kysymysryhmaid === kysymysryhmaid);
    return kayttoraja && kayttoraja.raja_ylitetty ? kayttoraja.vanhin_pvm : null;
};
const sortOppilaitos = (items: OppilaitosType[], lang: string) =>
    items.sort((a, b) => {
        const aName = a.name[lang as keyof TextType]?.toLowerCase() || '';
        const bName = b.name[lang as keyof TextType]?.toLowerCase() || '';
        return aName < bName ? -1 : 1;
    });

export function sortItems(items: OppilaitosSetType, lang: string) {
    const newSet: OppilaitosSetType = getDefaultEmptySet();

    newSet.grouped = items.grouped.map((group) => ({
        ...group,
        oppilaitokset: sortOppilaitos(group.oppilaitokset, lang),
    }));

    newSet.ungrouped = items.ungrouped.map((group) => ({
        ...group,
        oppilaitokset:
            group.oppilaitokset.length > 0
                ? sortOppilaitos(group.oppilaitokset, lang)
                : [],
    }));

    return newSet;
}

export const flattenItems = (itemSet: OppilaitosSetType, lang: string) =>
    sortOppilaitos(
        itemSet.grouped
            .flatMap((group) => group.oppilaitokset)
            .concat(itemSet.ungrouped[0]?.oppilaitokset),
        lang,
    );
