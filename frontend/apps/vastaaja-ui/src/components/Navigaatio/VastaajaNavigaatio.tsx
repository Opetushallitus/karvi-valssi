import Logo from '@cscfi/shared/components/Navigaatio/Logo';
import styles from '@cscfi/shared/components/Navigaatio/Navigaatio.module.css';

function VastaajaNavigaatio() {
    return (
        <nav>
            <div className={styles.logo}>
                <Logo />
            </div>
        </nav>
    );
}
export default VastaajaNavigaatio;
