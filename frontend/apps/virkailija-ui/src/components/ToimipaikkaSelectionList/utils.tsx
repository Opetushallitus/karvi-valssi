import {
    OppilaitosSetType,
    OppilaitosType,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import {getDefaultEmptySet, intersection, union} from '../../utils/helpers';

export function itemsIntersection(a: OppilaitosSetType, b: OppilaitosSetType) {
    const newSet: OppilaitosSetType = getDefaultEmptySet();

    newSet.grouped = a.grouped
        .filter((groupA) => b.grouped?.find((groupB) => groupA.id === groupB.id))
        .map((groupA) => {
            const groupB = b.grouped?.find((gb) => groupA.id === gb.id);
            return {
                ...groupA,
                oppilaitokset: groupA.oppilaitokset.filter(
                    (ol) => groupB?.oppilaitokset.indexOf(ol) !== -1,
                ),
            };
        });

    newSet.ungrouped[0].oppilaitokset = intersection(
        a.ungrouped[0].oppilaitokset,
        b.ungrouped[0].oppilaitokset,
    );

    return newSet;
}

export function itemsUnion(a: OppilaitosSetType, b: OppilaitosSetType) {
    const newSet: OppilaitosSetType = getDefaultEmptySet();

    a.grouped.forEach((groupA) => {
        const retGroup = newSet.grouped.find((newGroup) => newGroup.id === groupA.id);
        if (!retGroup) {
            newSet.grouped.push(groupA);
        } else {
            groupA.oppilaitokset.forEach((ol) => {
                if (!retGroup.oppilaitokset.includes(ol)) retGroup.oppilaitokset.push(ol);
            });
        }
    });

    b.grouped.forEach((groupB) => {
        const retGroup = newSet.grouped.find((newGroup) => newGroup.id === groupB.id);
        if (!retGroup) {
            newSet.grouped.push(groupB);
        } else {
            groupB.oppilaitokset.forEach((ol) => {
                if (!retGroup.oppilaitokset.includes(ol)) retGroup.oppilaitokset.push(ol);
            });
        }
    });

    newSet.ungrouped[0].oppilaitokset = union(
        a.ungrouped[0].oppilaitokset,
        b.ungrouped[0].oppilaitokset,
    );

    return newSet;
}

const filterOppilaitos = (items: OppilaitosType[], keyWord: string, lang: string) => {
    const kw = keyWord.trim().toLowerCase();
    if (kw !== '') {
        return items.filter((item) =>
            item.name[lang as keyof TextType]?.toLowerCase().includes(kw),
        );
    }
    return items;
};

export function filterItems(items: OppilaitosSetType, keyWord: string, lang: string) {
    const newSet: OppilaitosSetType = getDefaultEmptySet();

    newSet.grouped = items.grouped.map((group) => ({
        ...group,
        oppilaitokset: filterOppilaitos(group.oppilaitokset, keyWord, lang),
    }));

    newSet.ungrouped = items.ungrouped.map((group) => ({
        ...group,
        oppilaitokset: filterOppilaitos(group.oppilaitokset, keyWord, lang),
    }));

    return newSet;
}
