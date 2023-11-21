import {Dispatch, SetStateAction} from 'react';
import {KyselyType, KysymysType} from '@cscfi/shared/services/Data/Data-service';
import {arvoDeleteHttp$} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';

function getNewKysymyksetArray(
    currentKysymykset: KysymysType[],
    updatedKysymysId: number,
    deleteKysymys: boolean,
    updatedKysymys?: KysymysType,
): KysymysType[] | null {
    if (updatedKysymys) {
        const updatedKysymysIndex = currentKysymykset.findIndex(
            (kysymys) => kysymys.id === updatedKysymys.id,
        );
        if (updatedKysymysIndex === -1) {
            // new kysymys
            return [...currentKysymykset, updatedKysymys];
        }
        // replace current kysymys with the updated kysymys
        return [
            ...currentKysymykset.slice(0, updatedKysymysIndex),
            updatedKysymys,
            ...currentKysymykset.slice(updatedKysymysIndex + 1),
        ];
    }

    if (deleteKysymys && updatedKysymysId !== -1) {
        const updatedKysymysIndex = currentKysymykset.findIndex(
            (kysymys) => kysymys.id === updatedKysymysId,
        );
        if (updatedKysymysIndex === -1) {
            return currentKysymykset;
        }
        return [
            ...currentKysymykset.slice(0, updatedKysymysIndex),
            ...currentKysymykset.slice(updatedKysymysIndex + 1),
        ];
    }

    return null;
}

const handleError = (selectedKyselyId: number) =>
    console.log(`Error: Could not update kysely! Kysely-id: ${selectedKyselyId}`);

const updateOneKysely = (
    kysely: KyselyType,
    setKysely: Dispatch<SetStateAction<KyselyType | null>>,
    updatedKysymys?: KysymysType,
    updatedKysymysId: number = -1,
    deleteKysymys: boolean = false,
) => {
    if ((updatedKysymysId === -1 && deleteKysymys) || (deleteKysymys && updatedKysymys)) {
        handleError(kysely.id);
    }
    const newKysymykset = getNewKysymyksetArray(
        kysely.kysymykset,
        updatedKysymysId,
        deleteKysymys,
        updatedKysymys,
    );
    if (newKysymykset) {
        const newKysely = {...kysely};
        newKysely.kysymykset = newKysymykset;

        if (deleteKysymys) {
            arvoDeleteHttp$(`kysymys/${updatedKysymysId}`).subscribe(() =>
                setKysely(newKysely),
            );
        } else {
            setKysely(newKysely);
        }
    } else {
        handleError(kysely.id);
    }
};

export default updateOneKysely;
