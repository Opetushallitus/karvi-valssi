import {useTranslation} from 'react-i18next';
import {Link} from 'react-router-dom';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import styles from './EtusivuKyselytList.module.css';

interface KyselyLinkProps {
    kysely: KyselyType;
}

function KyselyLink({kysely}: KyselyLinkProps) {
    const {id, topic} = kysely;
    const {
        i18n: {language: lang},
    } = useTranslation(['esikatselu']);
    return (
        <Link className={styles.kyselylink} to={`/esikatselu?id=${id}`}>
            {topic[lang as keyof TextType]}
        </Link>
    );
}

export default KyselyLink;
