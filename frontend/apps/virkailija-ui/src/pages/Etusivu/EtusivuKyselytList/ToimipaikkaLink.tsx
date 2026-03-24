import {uniqueNumber} from '@cscfi/shared/utils/helpers';
import styles from './EtusivuKyselytList.module.css';
import ButtonWithLink from '../../../components/ButtonWithLink/ButtonWithLink';

type ToimipaikkaLinkProps = {
    toimipaikkaNimi: string;
    linkTo: string;
    linkText: string;
};

function ToimipaikkaLink({toimipaikkaNimi, linkTo, linkText}: ToimipaikkaLinkProps) {
    return (
        <div
            key={`${toimipaikkaNimi}_${uniqueNumber()}`}
            className={styles['kysely-toimipaikka-container']}
        >
            <div className={styles['kysely-toimipaikka-nimi']}>{toimipaikkaNimi}</div>
            <div className={styles['kysely-toimipaikka-buttons']}>
                <ButtonWithLink linkTo={linkTo} linkText={linkText} className="small" />
            </div>
        </div>
    );
}

export default ToimipaikkaLink;
