import {KyselyType, KysymysType} from '@cscfi/shared/services/Data/Data-service';

const getKysymysFromKysely = (
    kysely: KyselyType,
    selectedKysymysId: number,
): KysymysType | null => {
    if (kysely === undefined) {
        console.error('Error: kysely is undefined');
        return null;
    }

    const kysymys = kysely.kysymykset.find(
        (selectedKysymys: KysymysType) => selectedKysymys.id === selectedKysymysId,
    );
    if (kysymys === undefined) {
        console.error(`Error: Could not fetch kysymys with id: ${selectedKysymysId}`);
        return null;
    }

    return kysymys;
};

export default getKysymysFromKysely;
