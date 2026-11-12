use serde::{Deserialize, Serialize};
use url::Url;

// Deliberately no Debug/Display: the descriptor contains a session secret.
#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SessionDescriptor {
    pub base_url: String,
    pub token: String,
}

impl SessionDescriptor {
    pub fn validate(&self) -> Result<(), &'static str> {
        let url = Url::parse(&self.base_url).map_err(|_| "invalid_session_descriptor")?;
        if url.scheme() != "http"
            || url.host_str() != Some("127.0.0.1")
            || !matches!(url.port(), Some(1..=65535))
            || url.path() != "/"
            || url.query().is_some()
            || url.fragment().is_some()
            || !url.username().is_empty()
            || url.password().is_some()
            || self.token.len() != 43
            || !self.token.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
        {
            return Err("invalid_session_descriptor");
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::SessionDescriptor;

    fn descriptor(base_url: &str, token: &str) -> SessionDescriptor {
        SessionDescriptor { base_url: base_url.into(), token: token.into() }
    }

    #[test]
    fn descriptor_accepts_valid_loopback() {
        assert!(descriptor("http://127.0.0.1:49231", &"a".repeat(43)).validate().is_ok());
        assert!(descriptor("http://127.0.0.1:1/", &"_".repeat(43)).validate().is_ok());
        assert!(descriptor("http://127.0.0.1:65535/", &"-".repeat(43)).validate().is_ok());
    }

    #[test]
    fn descriptor_rejects_userinfo_query_fragment_unknown_fields() {
        for address in [
            "http://user@127.0.0.1:49231/", "http://user:pass@127.0.0.1:49231/",
            "http://127.0.0.1:49231/?token=x", "http://127.0.0.1:49231/#fragment",
        ] {
            assert!(descriptor(address, &"a".repeat(43)).validate().is_err());
        }
        let payload = serde_json::json!({"base_url": "http://127.0.0.1:49231", "token": "a".repeat(43), "extra": true});
        assert!(serde_json::from_value::<SessionDescriptor>(payload).is_err());
    }

    #[test]
    fn descriptor_preserves_url_and_token_validation() {
        for address in [
            "not a URL", "https://127.0.0.1:49231/", "http://example.org:49231/",
            "http://localhost:49231/", "http://[::1]:49231/", "http://127.0.0.1/",
            "http://127.0.0.1:0/", "http://127.0.0.1:65536/", "http://127.0.0.1:49231/v1",
        ] {
            assert!(descriptor(address, &"a".repeat(43)).validate().is_err());
        }
        for token in [String::new(), "a".repeat(42), "a".repeat(44), "!".repeat(43), "é".repeat(43)] {
            assert!(descriptor("http://127.0.0.1:49231", &token).validate().is_err());
        }
    }
}
