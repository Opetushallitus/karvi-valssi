import {Link} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import {KyselyType, StatusType, TextType} from '@cscfi/shared/services/Data/Data-service';
import {ArvoKysely} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import {kysymysRyhmaArvoKyselyMatch} from '@cscfi/shared/utils/helpers';
import Lock from '@mui/icons-material/Lock';
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

    const compareStrings = (a: object, b: object) => {
        const language = lang as keyof TextType;
        if (language === 'fi') {
            const aTitle = a?.topic?.fi ? a?.topic?.fi.toUpperCase() : '';
            const bTitle = b?.topic?.fi ? b?.topic?.fi.toUpperCase() : '';
            if (aTitle < bTitle) {
                return -1;
            }
            if (aTitle > bTitle) {
                return 1;
            }
            return 0;
        }
        if (language === 'sv' || language !== 'fi') {
            const aTitle = a?.topic?.sv ? a?.topic?.sv.toUpperCase() : '';
            const bTitle = b?.topic?.sv ? b?.topic?.sv.toUpperCase() : '';
            if (aTitle < bTitle) {
                return -1;
            }
            if (aTitle > bTitle) {
                return 1;
            }
            return 0;
        }
    };
    // the loop down there (looping through all kyselyt and checking each
    // against Arvokysely list) is O(n^2) complexity, but there should not be that many
    // ArvoKysely running at the same time (for each organization).
    return kyselyt.length > 0 ? (
        <ol className={styles['kysely-list']}>
            {kyselyt.sort(compareStrings).map((kysely: KyselyType) => {
                const {status, id, topic} = kysely;
                let tagStyles = '';
                let statusText = '';
                if (currentUserRole === ArvoRoles.YLLAPITAJA) {
                    switch (status) {
                        case StatusType.luonnos:
                            tagStyles = 'tag-inactive';
                            statusText = t('tag-julkaisematon');
                            break;
                        case StatusType.lukittu:
                            tagStyles = 'tag-inactive';
                            statusText = t('tag-lukittu');
                            break;
                        case StatusType.julkaistu:
                            tagStyles = 'tag-active';
                            statusText = t('tag-julkaistu');
                            break;
                        default:
                            break;
                    }
                } else if (
                    currentUserRole === ArvoRoles.PAAKAYTTAJA ||
                    currentUserRole === ArvoRoles.TOTEUTTAJA
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
                            <span className={styles[tagStyles]}>
                                {statusText}
                                {status === StatusType.lukittu && (
                                    <div title={t('tag-lukittu')}>
                                        <Lock />
                                    </div>
                                )}
                            </span>
                        </li>
                    );
                }
                return null;
            })}
        </ol>
    ) : null;
}

export default IndikattoritKyselytList;
