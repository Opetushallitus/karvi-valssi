import {useContext, useEffect, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import Grid from '@mui/material/Grid';
import {
    OppilaitosGroupType,
    virkailijapalveluGetAluejako$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import UserContext from '../../Context';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import ItemsList from '../../components/ToimipaikkaSelectionList/ItemsList';
import styles from './Aluejako.module.css';
import {getDefaultEmptySet} from '../../utils/helpers';

function Aluejako() {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['aluejako']);
    const userInfo = useContext(UserContext);

    const [groups, setGroups] = useState<OppilaitosGroupType[]>(
        getDefaultEmptySet().grouped,
    );

    useEffect(() => {
        virkailijapalveluGetAluejako$(userInfo!)(
            userInfo?.arvoAktiivinenRooli.organisaatio || '',
        ).subscribe((alueet) => {
            setGroups(alueet.grouped);
        });
    }, [userInfo]);

    const groupList = () =>
        Object.values(groups).map((group) => (
            <Grid key={`group_${group.name[lang as keyof TextType]}_${uniqueNumber()}`}>
                <ItemsList
                    isLeft={false}
                    label={group.name[lang as keyof TextType]}
                    allItems={{
                        grouped: [],
                        ungrouped: [
                            {
                                ...getDefaultEmptySet().ungrouped[0],
                                oppilaitokset: group.oppilaitokset,
                            },
                        ],
                    }}
                    filter=""
                    setFilter={() => undefined}
                    checked={getDefaultEmptySet()}
                    setChecked={() => undefined}
                    selectableGroups={false}
                />
                <ButtonWithLink
                    linkText={t('painike-muokkaa-aluetta')}
                    linkTo={`./muokkaa/${group.id}`}
                />
            </Grid>
        ));

    return (
        <>
            <h1>{userInfo?.organisaatio}</h1>
            <h2 className={styles.groupsHeader}>{t('varhaiskasvatusalueet')}</h2>

            <Grid container spacing="2rem">
                {groupList()}
            </Grid>

            <div className="button-container">
                <ButtonWithLink linkTo="./uusi" linkText={t('painike-uusi-alue')} />
            </div>
        </>
    );
}

export default Aluejako;
