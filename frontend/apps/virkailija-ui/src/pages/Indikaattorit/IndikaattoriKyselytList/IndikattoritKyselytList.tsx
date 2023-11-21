import {Link} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import {KyselyType, StatusType, TextType} from '@cscfi/shared/services/Data/Data-service';
import {ArvoKysely} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {kysymysRyhmaArvoKyselyMatch} from '@cscfi/shared/utils/helpers';
import {ValssiUserLevel} from '../../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import styles from '../Indikaattorit.module.css';

interface IndikattoritKyselytListProps {
    kyselyt: KyselyType[];
    currentUserRole: string;
    arvoKyselyt: ArvoKysely[];
}
function IndikattoritKyselytList({
    kyselyt,
    currentUserRole,
    arvoKyselyt,
}: IndikattoritKyselytListProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['arvtyok']);
    // the loop down there (looping through all kyselyt and checking each
    // against Arvokysely list) is O(n^2) complexity, but there should not be that many
    // ArvoKysely running at the same time (for each organization).
    return kyselyt.length > 0 ? (
        <ol className={styles['kysely-list']}>
            {kyselyt.map((kysely: KyselyType) => {
                const {status, id, topic} = kysely;
                let tagStyles = '';
                let statusText = '';
                if (currentUserRole === ValssiUserLevel.YLLAPITAJA) {
                    tagStyles =
                        status !== StatusType.luonnos ? 'tag-active' : 'tag-inactive';
                    if (status === StatusType.luonnos) {
                        statusText = t('tag-julkaisematon');
                    } else if (status === StatusType.julkaistu) {
                        statusText = t('tag-julkaistu');
                    }
                } else if (
                    currentUserRole === ValssiUserLevel.PAAKAYTTAJA ||
                    currentUserRole === ValssiUserLevel.TOTEUTTAJA
                ) {
                    tagStyles = 'tag-inactive';
                    statusText = t('tag-aktivoimaton');
                    // do we have ArvoKysely for this kysymysryhma id?
                    // if ArvoKysely is created,
                    // then the questionnaire is activated.

                    if (
                        arvoKyselyt?.some((arvoKysely) =>
                            kysymysRyhmaArvoKyselyMatch(arvoKysely, id),
                        )
                    ) {
                        tagStyles = 'tag-active';
                        statusText = t('tag-aktivoitu');
                    }
                }
                if (kysely.status !== StatusType.arkistoitu) {
                    return (
                        <li key={id}>
                            <Link
                                className={styles.link}
                                to={`/esikatselu?id=${id}`}
                                state={{prevPath: 'indikaattorit'}}
                            >
                                {topic[lang as keyof TextType]}
                            </Link>
                            <span className={styles[tagStyles]}>{statusText}</span>
                        </li>
                    );
                }
                return null;
            })}
        </ol>
    ) : null;
}

export default IndikattoritKyselytList;
